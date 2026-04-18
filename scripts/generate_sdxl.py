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


def main(argv: Optional[Sequence[str]] = None) -> None:
    argv_list = list(argv) if argv is not None else sys.argv[1:]
    args = parse_args(argv)
    config = load_config()
    apply_config_defaults(args, argv_list, config["defaults"])
    apply_resolution_preset(args, argv_list, config["presets"])
    ensure_prompt(args)
    device = resolve_device(args.device)
    dtype = torch.float16 if device == "cuda" else torch.float32

    pipe = build_pipeline(args.model, device, dtype)

    generator = None
    if args.seed is not None:
        generator = torch.Generator(device=device).manual_seed(args.seed)

    result = pipe(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        width=args.width,
        height=args.height,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance_scale,
        generator=generator,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"sdxl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    output_path = output_dir / filename
    result.images[0].save(output_path)

    print(f"Saved image to: {output_path}")


if __name__ == "__main__":
    main()
