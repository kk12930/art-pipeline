import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.server import app


class ApiTests(unittest.TestCase):
    def test_health_returns_ok(self) -> None:
        client = TestClient(app)

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_generate_returns_saved_path(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.yaml").write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  device: cpu\npresets:\n  square:\n    width: 512\n    height: 512\n""",
                encoding="utf-8",
            )

            with patch("api.server.generate_sdxl.build_pipeline", return_value=fake_pipe) as build_pipeline:
                with patch("api.server.generate_sdxl.Path.cwd", return_value=root):
                    response = client.post(
                        "/generate",
                        json={
                            "prompt": "api prompt",
                            "device": "cpu",
                            "output_dir": temp_dir,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        build_pipeline.assert_called_once()
        fake_pipe.assert_called_once()
        fake_image.save.assert_called_once()
        saved_path = Path(response.json()["outputPath"])
        self.assertEqual(saved_path.parent.name, Path(temp_dir).name)

    def test_generate_returns_400_for_missing_lora(self) -> None:
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.yaml").write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  device: cpu\npresets: {}\n""",
                encoding="utf-8",
            )

            with patch("api.server.generate_sdxl.Path.cwd", return_value=root):
                response = client.post(
                    "/generate",
                    json={
                        "prompt": "api prompt",
                        "device": "cpu",
                        "lora_path": str(root / "missing-lora.safetensors"),
                        "output_dir": temp_dir,
                    },
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("LoRA weights not found", response.json()["detail"])

    def test_generate_uses_config_prompt_when_request_prompt_missing(self) -> None:
        fake_image = MagicMock()
        fake_pipe = MagicMock()
        fake_pipe.return_value = MagicMock(images=[fake_image])
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config.yaml").write_text(
                """defaults:\n  prompt: config prompt\n  model: config-model\n  device: cpu\npresets: {}\n""",
                encoding="utf-8",
            )

            with patch("api.server.generate_sdxl.build_pipeline", return_value=fake_pipe):
                with patch("api.server.generate_sdxl.Path.cwd", return_value=root):
                    response = client.post(
                        "/generate",
                        json={
                            "device": "cpu",
                            "output_dir": temp_dir,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        call_kwargs = fake_pipe.call_args.kwargs
        self.assertEqual(call_kwargs["prompt"], "config prompt")


if __name__ == "__main__":
    unittest.main()
