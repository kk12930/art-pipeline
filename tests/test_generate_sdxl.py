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


if __name__ == "__main__":
    unittest.main()
