from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from scripts import generate_sdxl


class GenerateRequest(BaseModel):
    prompt: Optional[str] = None
    model: Optional[str] = None
    negative_prompt: Optional[str] = Field(default=None, alias="negativePrompt")
    width: Optional[int] = None
    height: Optional[int] = None
    preset: Optional[str] = None
    steps: Optional[int] = None
    guidance_scale: Optional[float] = Field(default=None, alias="guidanceScale")
    seed: Optional[int] = None
    device: Optional[str] = None
    output_dir: Optional[str] = Field(default=None, alias="outputDir")
    lora_path: Optional[str] = Field(default=None, alias="loraPath")

    model_config = {"populate_by_name": True}


class GenerateResponse(BaseModel):
    output_path: str = Field(alias="outputPath")

    model_config = {"populate_by_name": True}


app = FastAPI(title="art-pipeline API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    if request.lora_path is not None and not Path(request.lora_path).exists():
        raise HTTPException(status_code=400, detail=f"LoRA weights not found: {request.lora_path}")

    argv: list[str] = []
    if request.prompt is not None:
        argv.extend(["--prompt", request.prompt])
    if request.model is not None:
        argv.extend(["--model", request.model])
    if request.negative_prompt is not None:
        argv.extend(["--negative-prompt", request.negative_prompt])
    if request.width is not None:
        argv.extend(["--width", str(request.width)])
    if request.height is not None:
        argv.extend(["--height", str(request.height)])
    if request.preset is not None:
        argv.extend(["--preset", request.preset])
    if request.steps is not None:
        argv.extend(["--steps", str(request.steps)])
    if request.guidance_scale is not None:
        argv.extend(["--guidance-scale", str(request.guidance_scale)])
    if request.seed is not None:
        argv.extend(["--seed", str(request.seed)])
    if request.device is not None:
        argv.extend(["--device", request.device])
    if request.output_dir is not None:
        argv.extend(["--output-dir", request.output_dir])
    if request.lora_path is not None:
        argv.extend(["--lora-path", request.lora_path])

    try:
        args, config, argv_list = generate_sdxl.build_runtime_args(argv)
        output_paths = generate_sdxl.run_generation(args, config, argv_list)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return GenerateResponse(outputPath=str(Path(output_paths[0])))
