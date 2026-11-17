#!/usr/bin/env python3
"""CPU-only text-to-3D generation with OpenAI Shap-E."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PROMPT_FILE = Path(__file__).parent / "prompts" / "nader_shah_afshar.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a 3D mesh on CPU with Shap-E.")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT_FILE)
    parser.add_argument("--steps", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/nader_shah_afshar"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = args.prompt.strip() if args.prompt and args.prompt.strip() else ""
    if not prompt and args.prompt_file.is_file():
        prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    if not prompt:
        raise SystemExit("No prompt supplied.")
    if not 8 <= args.steps <= 64:
        raise SystemExit("--steps must be between 8 and 64.")

    os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parent / ".models" / "huggingface"))
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import torch
    import trimesh
    from diffusers import ShapEPipeline
    from diffusers.utils import export_to_ply

    threads = max(1, int(os.environ.get("CPU_THREADS", os.cpu_count() or 2)))
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(max(1, min(4, threads)))
    torch.manual_seed(args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = "nader_shah_afshar"
    ply_path = args.output_dir / f"{stem}.ply"
    glb_path = args.output_dir / f"{stem}.glb"

    print("Device: CPU only", flush=True)
    print(f"CPU threads: {threads}", flush=True)
    print("Loading openai/shap-e weights from Hugging Face...", flush=True)
    pipe = ShapEPipeline.from_pretrained(
        "openai/shap-e",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    pipe = pipe.to("cpu")
    pipe.set_progress_bar_config(disable=False)

    print(f"Generating mesh with {args.steps} diffusion steps...", flush=True)
    with torch.inference_mode():
        result = pipe(
            prompt,
            guidance_scale=15.0,
            num_inference_steps=args.steps,
            frame_size=256,
            output_type="mesh",
        )

    print("Exporting PLY...", flush=True)
    export_to_ply(result.images[0], str(ply_path))
    loaded = trimesh.load(str(ply_path), force="scene", process=False)
    if isinstance(loaded, trimesh.Scene):
        geometries = [g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not geometries:
            raise RuntimeError("Shap-E returned no polygon mesh.")
        mesh = trimesh.util.concatenate(geometries)
    else:
        mesh = loaded
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise RuntimeError("Generated mesh is empty.")
    mesh.export(str(glb_path), file_type="glb")

    metadata = {
        "asset_name": "Nader Shah Afshar",
        "model_id": "openai/shap-e",
        "device": "cpu",
        "prompt": prompt,
        "seed": args.seed,
        "steps": args.steps,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": {"glb": glb_path.name, "ply": ply_path.name},
        "quality_note": "CPU Shap-E output; inspect mesh and vertex colors/materials before production use.",
    }
    (args.output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"GLB: {glb_path.resolve()}", flush=True)
    print(f"PLY: {ply_path.resolve()}", flush=True)
    print("Generation completed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
