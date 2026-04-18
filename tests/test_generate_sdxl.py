import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import torch

from scripts import generate_sdxl


class GenerateSdxlTests(unittest.TestCase):
    def test_parse_args_reads_required_values(self) -> None:
        args = generate_sdxl.parse_args([
            "--prompt",
            "test icon",
            "--width",
            "512",
            "--height",
            "512",
        ])

        self.assertEqual(args.prompt, "test icon")
        self.assertEqual(args.width, 512)
        self.assertEqual(args.height, 512)
        self.assertEqual(args.output_dir, "outputs")

    def test_resolve_device_auto_uses_cuda_when_available(self) -> None:
        with patch.object(torch.cuda, "is_available", return_value=True):
            self.assertEqual(generate_sdxl.resolve_device("auto"), "cuda")

    def test_resolve_device_auto_falls_back_to_cpu_when_cuda_unavailable(self) -> None:
        with patch.object(torch.cuda, "is_available", return_value=False):
            self.assertEqual(generate_sdxl.resolve_device("auto"), "cpu")

    def test_resolve_device_returns_cpu(self) -> None:
        self.assertEqual(generate_sdxl.resolve_device("cpu"), "cpu")

    def test_resolve_device_cuda_raises_when_unavailable(self) -> None:
        with patch.object(torch.cuda, "is_available", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "CUDA requested but not available"):
                generate_sdxl.resolve_device("cuda")

    def test_main_saves_generated_image(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  width: 640\n  height: 640\n  steps: 12\n  guidance_scale: 5.5\n  seed: 123\n  device: cpu\npresets:\n  square:\n    width: 512\n    height: 512\n""",
                encoding="utf-8",
            )
            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe) as build_pipeline:
                with patch.object(generate_sdxl.Path, "cwd", return_value=Path(temp_dir)):
                    generate_sdxl.main([
                        "--output-dir",
                        temp_dir,
                    ])

        build_pipeline.assert_called_once_with(
            "config-model",
            "cpu",
            torch.float32,
        )
        fake_pipe.assert_called_once()
        fake_image.save.assert_called_once()
        saved_path = Path(fake_image.save.call_args[0][0])
        self.assertEqual(saved_path.parent.name, Path(temp_dir).name)
        self.assertEqual(build_pipeline.call_args.args[0], "config-model")

    def test_main_uses_preset_when_cli_does_not_override_resolution(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  width: 640\n  height: 640\n  device: cpu\npresets:\n  widescreen:\n    width: 1280\n    height: 720\n""",
                encoding="utf-8",
            )
            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe) as build_pipeline:
                with patch.object(generate_sdxl.Path, "cwd", return_value=Path(temp_dir)):
                    generate_sdxl.main([
                        "--preset",
                        "widescreen",
                        "--output-dir",
                        temp_dir,
                    ])

        fake_pipe.assert_called_once()
        call_kwargs = fake_pipe.call_args.kwargs
        self.assertEqual(call_kwargs["width"], 1280)
        self.assertEqual(call_kwargs["height"], 720)

    def test_main_prefers_cli_dimensions_over_config_and_preset_with_equals_sign(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  width: 640\n  height: 640\n  device: cpu\npresets:\n  widescreen:\n    width: 1280\n    height: 720\n""",
                encoding="utf-8",
            )
            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe):
                with patch.object(generate_sdxl.Path, "cwd", return_value=Path(temp_dir)):
                    generate_sdxl.main([
                        "--preset=widescreen",
                        "--width=900",
                        "--height=600",
                        "--output-dir",
                        temp_dir,
                    ])

        call_kwargs = fake_pipe.call_args.kwargs
        self.assertEqual(call_kwargs["width"], 900)
        self.assertEqual(call_kwargs["height"], 600)

    def test_main_uses_config_prompt_when_cli_prompt_missing(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(
                """defaults:\n  prompt: config prompt\n  device: cpu\n  model: config-model\npresets:\n  square:\n    width: 512\n    height: 512\n""",
                encoding="utf-8",
            )
            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe):
                with patch.object(generate_sdxl.Path, "cwd", return_value=Path(temp_dir)):
                    generate_sdxl.main([
                        "--output-dir",
                        temp_dir,
                    ])

        call_kwargs = fake_pipe.call_args.kwargs
        self.assertEqual(call_kwargs["prompt"], "config prompt")

    def test_main_raises_for_unknown_preset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(
                """defaults:\n  prompt: config prompt\npresets:\n  square:\n    width: 512\n    height: 512\n""",
                encoding="utf-8",
            )
            with patch.object(generate_sdxl.Path, "cwd", return_value=Path(temp_dir)):
                with self.assertRaisesRegex(ValueError, "Unknown preset 'missing'"):
                    generate_sdxl.main([
                        "--preset",
                        "missing",
                    ])

    def test_load_config_reads_default_generation_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  width: 768\npresets:\n  square:\n    width: 512\n    height: 512\n""",
                encoding="utf-8",
            )

            config = generate_sdxl.load_config(config_path)

        self.assertEqual(config["defaults"]["model"], "config-model")
        self.assertEqual(config["defaults"]["width"], 768)
        self.assertEqual(config["defaults"]["prompt"], "config prompt")
        self.assertEqual(config["presets"]["square"]["height"], 512)

    def test_parse_args_reads_batch_file(self) -> None:
        args = generate_sdxl.parse_args([
            "--batch-file",
            "batch.yaml",
        ])

        self.assertEqual(args.batch_file, "batch.yaml")

    def test_parse_args_reads_lora_path(self) -> None:
        args = generate_sdxl.parse_args([
            "--lora-path",
            "models/example-lora.safetensors",
        ])

        self.assertEqual(args.lora_path, "models/example-lora.safetensors")

    def test_load_batch_items_reads_items_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_path = Path(temp_dir) / "batch.yaml"
            batch_path.write_text(
                """items:\n  - prompt: first\n    preset: square\n  - prompt: second\n    width: 640\n    height: 640\n""",
                encoding="utf-8",
            )

            items = generate_sdxl.load_batch_items(batch_path)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["preset"], "square")
        self.assertEqual(items[1]["width"], 640)

    def test_main_runs_batch_items_with_fail_fast(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.yaml").write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  negative_prompt: config negative\n  width: 320\n  height: 320\n  steps: 12\n  guidance_scale: 5.5\n  device: cpu\npresets:\n  square:\n    width: 1024\n    height: 1024\n""",
                encoding="utf-8",
            )
            (root / "batch.yaml").write_text(
                """items:\n  - prompt: first prompt\n    preset: square\n  - prompt: second prompt\n    width: 640\n    height: 480\n""",
                encoding="utf-8",
            )

            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe) as build_pipeline:
                with patch.object(generate_sdxl.Path, "cwd", return_value=root):
                    generate_sdxl.main([
                        "--batch-file",
                        str(root / "batch.yaml"),
                        "--output-dir",
                        temp_dir,
                    ])

        build_pipeline.assert_called_once_with(
            "config-model",
            "cpu",
            torch.float32,
        )
        self.assertEqual(fake_pipe.call_count, 2)
        first_kwargs = fake_pipe.call_args_list[0].kwargs
        second_kwargs = fake_pipe.call_args_list[1].kwargs
        self.assertEqual(first_kwargs["prompt"], "first prompt")
        self.assertEqual(first_kwargs["width"], 1024)
        self.assertEqual(first_kwargs["height"], 1024)
        self.assertEqual(second_kwargs["prompt"], "second prompt")
        self.assertEqual(second_kwargs["width"], 640)
        self.assertEqual(second_kwargs["height"], 480)
        self.assertEqual(fake_image.save.call_count, 2)

    def test_main_batch_respects_cli_dimensions_over_batch_item(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.yaml").write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  width: 320\n  height: 320\n  device: cpu\npresets:\n  square:\n    width: 1024\n    height: 1024\n""",
                encoding="utf-8",
            )
            (root / "batch.yaml").write_text(
                """items:\n  - prompt: first prompt\n    width: 640\n    height: 480\n""",
                encoding="utf-8",
            )

            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe):
                with patch.object(generate_sdxl.Path, "cwd", return_value=root):
                    generate_sdxl.main([
                        "--batch-file",
                        str(root / "batch.yaml"),
                        "--width=900",
                        "--height=600",
                        "--output-dir",
                        temp_dir,
                    ])

        call_kwargs = fake_pipe.call_args.kwargs
        self.assertEqual(call_kwargs["width"], 900)
        self.assertEqual(call_kwargs["height"], 600)

    def test_main_batch_stops_on_first_error(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.side_effect = [
            MagicMock(images=[fake_image]),
            RuntimeError("pipeline exploded"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.yaml").write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  device: cpu\npresets: {}\n""",
                encoding="utf-8",
            )
            (root / "batch.yaml").write_text(
                """items:\n  - prompt: first prompt\n  - prompt: second prompt\n  - prompt: third prompt\n""",
                encoding="utf-8",
            )

            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe):
                with patch.object(generate_sdxl.Path, "cwd", return_value=root):
                    with self.assertRaisesRegex(RuntimeError, "pipeline exploded"):
                        generate_sdxl.main([
                            "--batch-file",
                            str(root / "batch.yaml"),
                            "--output-dir",
                            temp_dir,
                        ])

        self.assertEqual(fake_pipe.call_count, 2)
        fake_image.save.assert_called_once()

    def test_apply_lora_weights_loads_existing_path(self) -> None:
        fake_pipe = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            lora_path = Path(temp_dir) / "example-lora.safetensors"
            lora_path.write_bytes(b"test")

            generate_sdxl.apply_lora_weights(fake_pipe, str(lora_path))

        fake_pipe.load_lora_weights.assert_called_once_with(str(lora_path))

    def test_apply_lora_weights_raises_for_missing_path(self) -> None:
        fake_pipe = MagicMock()

        with self.assertRaisesRegex(FileNotFoundError, "LoRA weights not found"):
            generate_sdxl.apply_lora_weights(fake_pipe, "missing-lora.safetensors")

    def test_main_loads_lora_before_generation(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lora_path = root / "example-lora.safetensors"
            lora_path.write_bytes(b"test")
            (root / "config.yaml").write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  device: cpu\npresets:\n  square:\n    width: 512\n    height: 512\n""",
                encoding="utf-8",
            )

            with patch.object(generate_sdxl, "build_pipeline", return_value=fake_pipe):
                with patch.object(generate_sdxl.Path, "cwd", return_value=root):
                    generate_sdxl.main([
                        "--lora-path",
                        str(lora_path),
                        "--output-dir",
                        temp_dir,
                    ])

        fake_pipe.load_lora_weights.assert_called_once_with(str(lora_path))
        fake_pipe.assert_called_once()


if __name__ == "__main__":
    unittest.main()
