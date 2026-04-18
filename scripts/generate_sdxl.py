import argparse
import importlib
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Protocol, Sequence, cast

import torch
import yaml

if TYPE_CHECKING:
    from PIL.Image import Image


class PipelineResult(Protocol):
    images: list["Image"]


class SdxlPipeline(Protocol):
    @classmethod
    def from_pretrained(
        cls,
        pretrained_model_name_or_path: str,
        *,
        torch_dtype: torch.dtype,
        use_safetensors: bool,
    ) -> "SdxlPipeline": ...

    def to(self, device: str) -> "SdxlPipeline": ...

    def enable_attention_slicing(self) -> None: ...

    def load_lora_weights(self, pretrained_model_name_or_path_or_dict: str) -> None: ...

    def __call__(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        num_inference_steps: int,
        guidance_scale: float,
        generator: Optional[torch.Generator],
    ) -> PipelineResult: ...


BATCH_ITEM_FLAG_MAP = {
    "prompt": "--prompt",
    "negative_prompt": "--negative-prompt",
    "width": "--width",
    "height": "--height",
    "preset": "--preset",
    "steps": "--steps",
    "guidance_scale": "--guidance-scale",
    "seed": "--seed",
    "output_dir": "--output-dir",
}

BATCH_ITEM_ALLOWED_FIELDS = set(BATCH_ITEM_FLAG_MAP)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one image with SDXL.")
    parser.add_argument("--prompt", default=None, help="Prompt for image generation.")
    parser.add_argument(
        "--model",
        default="stabilityai/stable-diffusion-xl-base-1.0",
        help="Hugging Face model ID or local model path.",
    )
    parser.add_argument(
        "--negative-prompt",
        default="blurry, low quality, distorted, text, watermark",
        help="Negative prompt.",
    )
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--preset", default=None, help="Named resolution preset from config.yaml.")
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--guidance-scale", type=float, default=7.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--output-dir", default="outputs", help="Directory for generated images.")
    parser.add_argument("--batch-file", default=None, help="YAML file describing sequential batch items.")
    parser.add_argument("--lora-path", default=None, help="Optional local LoRA weights path for inference.")
    return parser.parse_args(argv)


def load_config(config_path: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    if config_path is None:
        config_path = Path.cwd() / "config.yaml"

    if not config_path.exists():
        return {"defaults": {}, "presets": {}}

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError("config.yaml must contain a mapping at the top level.")

    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("config.yaml defaults must be a mapping.")

    presets = data.get("presets", {})
    if not isinstance(presets, dict):
        raise ValueError("config.yaml presets must be a mapping.")

    return {"defaults": defaults, "presets": presets}


def load_batch_items(batch_path: Path) -> list[dict[str, Any]]:
    if not batch_path.exists():
        raise FileNotFoundError(f"Batch file not found: {batch_path}")

    with batch_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError("batch.yaml must contain a mapping at the top level.")

    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("batch.yaml must contain an 'items' list.")

    if not items:
        raise ValueError("batch.yaml items must not be empty.")

    validated_items: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"batch.yaml item {index} must be a mapping.")

        unknown_fields = sorted(set(item) - BATCH_ITEM_ALLOWED_FIELDS)
        if unknown_fields:
            joined = ", ".join(unknown_fields)
            raise ValueError(f"batch.yaml item {index} has unsupported fields: {joined}")

        validated_items.append(item)

    return validated_items


def apply_config_defaults(
    args: argparse.Namespace,
    argv: Sequence[str],
    config_defaults: dict[str, Any],
) -> None:
    flag_map = {
        "prompt": "--prompt",
        "model": "--model",
        "negative_prompt": "--negative-prompt",
        "width": "--width",
        "height": "--height",
        "steps": "--steps",
        "guidance_scale": "--guidance-scale",
        "seed": "--seed",
        "device": "--device",
    }

    for field, flag in flag_map.items():
        if argument_was_provided(argv, flag):
            continue

        value = config_defaults.get(field)
        if value is not None or field == "seed":
            setattr(args, field, value)


def apply_resolution_preset(
    args: argparse.Namespace,
    argv: Sequence[str],
    presets: dict[str, Any],
) -> None:
    if not args.preset:
        return

    preset = presets.get(args.preset)
    if not isinstance(preset, dict):
        available = ", ".join(sorted(presets)) or "<none>"
        raise ValueError(f"Unknown preset '{args.preset}'. Available presets: {available}")

    for field in ("width", "height"):
        flag = f"--{field}"
        if argument_was_provided(argv, flag):
            continue

        value = preset.get(field)
        if value is not None:
            setattr(args, field, value)


def ensure_prompt(args: argparse.Namespace) -> None:
    if not args.prompt:
        raise ValueError("A prompt is required either on the CLI or in config.yaml defaults.")


def argument_was_provided(argv: Sequence[str], flag: str) -> bool:
    return any(argument == flag or argument.startswith(f"{flag}=") for argument in argv)


def resolve_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but not available.")
    return device


def build_pipeline(model: str, device: str, dtype: torch.dtype) -> SdxlPipeline:
    diffusers_module = importlib.import_module("diffusers")
    pipeline_cls = cast(type[SdxlPipeline], getattr(diffusers_module, "StableDiffusionXLPipeline"))
    pipe = pipeline_cls.from_pretrained(
        model,
        torch_dtype=dtype,
        use_safetensors=True,
    )
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()
    return pipe


def apply_lora_weights(pipe: SdxlPipeline, lora_path: Optional[str]) -> None:
    if lora_path is None:
        return

    path = Path(lora_path)
    if not path.exists():
        raise FileNotFoundError(f"LoRA weights not found: {path}")

    pipe.load_lora_weights(str(path))


def build_generator(seed: Optional[int], device: str) -> Optional[torch.Generator]:
    if seed is None:
        return None

    return torch.Generator(device=device).manual_seed(seed)


def clone_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(**vars(args))


def build_runtime_args(argv: Optional[Sequence[str]] = None) -> tuple[argparse.Namespace, dict[str, dict[str, Any]], list[str]]:
    argv_list = list(argv) if argv is not None else sys.argv[1:]
    args = parse_args(argv)
    config = load_config()
    apply_config_defaults(args, argv_list, config["defaults"])
    apply_resolution_preset(args, argv_list, config["presets"])
    return args, config, argv_list


def apply_batch_item_overrides(
    base_args: argparse.Namespace,
    batch_item: dict[str, Any],
    argv: Sequence[str],
    presets: dict[str, Any],
) -> argparse.Namespace:
    item_args = clone_args(base_args)

    if "preset" in batch_item and not argument_was_provided(argv, "--preset"):
        item_args.preset = batch_item["preset"]
        apply_resolution_preset(item_args, argv, presets)

    for field, flag in BATCH_ITEM_FLAG_MAP.items():
        if field == "preset" or argument_was_provided(argv, flag) or field not in batch_item:
            continue

        setattr(item_args, field, batch_item[field])

    ensure_prompt(item_args)
    return item_args


def save_image(result: PipelineResult, output_dir: str, item_index: Optional[int] = None) -> Path:
    output_path_dir = Path(output_dir)
    output_path_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "sdxl" if item_index is None else f"sdxl_{item_index:03d}"
    output_path = output_path_dir / f"{prefix}_{timestamp}.png"
    result.images[0].save(output_path)
    return output_path


def generate_image(
    pipe: SdxlPipeline,
    args: argparse.Namespace,
    device: str,
    item_index: Optional[int] = None,
) -> Path:
    result = pipe(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        width=args.width,
        height=args.height,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance_scale,
        generator=build_generator(args.seed, device),
    )
    output_path = save_image(result, args.output_dir, item_index)
    print(f"Saved image to: {output_path}")
    return output_path


def run_generation(args: argparse.Namespace, config: dict[str, dict[str, Any]], argv_list: Sequence[str]) -> list[Path]:
    batch_items = None
    if args.batch_file is not None:
        batch_items = load_batch_items(Path(args.batch_file))
    else:
        ensure_prompt(args)

    device = resolve_device(args.device)
    dtype = torch.float16 if device == "cuda" else torch.float32

    pipe = build_pipeline(args.model, device, dtype)
    apply_lora_weights(pipe, args.lora_path)

    if batch_items is None:
        return [generate_image(pipe, args, device)]

    output_paths: list[Path] = []
    for item_index, batch_item in enumerate(batch_items, start=1):
        item_args = apply_batch_item_overrides(args, batch_item, argv_list, config["presets"])
        output_paths.append(generate_image(pipe, item_args, device, item_index=item_index))

    return output_paths


def main(argv: Optional[Sequence[str]] = None) -> None:
    args, config, argv_list = build_runtime_args(argv)
    _ = run_generation(args, config, argv_list)


if __name__ == "__main__":
    main()
