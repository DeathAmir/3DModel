#!/usr/bin/env python3
"""Generate a textured GLB asset with Microsoft's TRELLIS Text pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PROMPT_FILE = Path(__file__).parent / "prompts" / "nader_shah_afshar.txt"
DEFAULT_MODEL = "microsoft/TRELLIS-text-large"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a textured 3D GLB from a text prompt using TRELLIS."
    )
    parser.add_argument("--prompt", help="English text prompt.")
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT_FILE)
    parser.add_argument("--model-id", default=DEFAULT_MODEL)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--texture-size", type=int, default=2048)
    parser.add_argument("--simplify", type=float, default=0.95)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/nader_shah_afshar"))
    return parser.parse_args()


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt and args.prompt.strip():
        return args.prompt.strip()
    if args.prompt_file.is_file():
        prompt = args.prompt_file.read_text(encoding="utf-8").strip()
        if prompt:
            return prompt
    raise SystemExit(
        f"No prompt supplied. Use --prompt or provide a valid --prompt-file: {args.prompt_file}"
    )


def main() -> int:
    args = parse_args()
    prompt = load_prompt(args)

    if not 512 <= args.texture_size <= 4096:
        raise SystemExit("--texture-size must be between 512 and 4096.")
    if not 0.0 < args.simplify <= 1.0:
        raise SystemExit("--simplify must be greater than 0 and at most 1.")

    os.environ.setdefault("SPCONV_ALGO", "native")

    try:
        import torch
    except ImportError as exc:
        raise SystemExit(
            "PyTorch is missing. Install the official TRELLIS environment first."
        ) from exc

    if not torch.cuda.is_available():
        raise SystemExit(
            "TRELLIS requires a supported NVIDIA CUDA GPU (official project "
            "guidance: at least 16 GB VRAM). CUDA is not available in this "
            "Python environment. An AMD RX 580 / CPU-only machine cannot run "
            "this pipeline; use a compatible Linux NVIDIA GPU host."
        )

    trellis_root = Path(os.environ.get("TRELLIS_ROOT", Path(__file__).resolve().parent.parent / "TRELLIS")).expanduser()
    if trellis_root.is_dir() and str(trellis_root.resolve()) not in sys.path:
        sys.path.insert(0, str(trellis_root.resolve()))

    from trellis.pipelines import TrellisTextTo3DPipeline
    from trellis.utils import postprocessing_utils

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = "nader_shah_afshar"
    glb_path = args.output_dir / f"{stem}.glb"
    ply_path = args.output_dir / f"{stem}.ply"

    print(f"[1/4] Loading {args.model_id} from Hugging Face...")
    print("Weights are downloaded to the Hugging Face cache, not committed to Git.")
    pipeline = TrellisTextTo3DPipeline.from_pretrained(args.model_id)
    pipeline.cuda()

    print("[2/4] Generating 3D representation...")
    print(f"Prompt: {prompt}")
    outputs = pipeline.run(prompt, seed=args.seed)

    if not outputs.get("mesh") or not outputs.get("gaussian"):
        raise RuntimeError(
            "TRELLIS did not return both mesh and Gaussian outputs; "
            "cannot create the textured GLB."
        )

    print("[3/4] Extracting textured GLB...")
    glb = postprocessing_utils.to_glb(
        outputs["gaussian"][0],
        outputs["mesh"][0],
        simplify=args.simplify,
        texture_size=args.texture_size,
    )
    glb.export(str(glb_path))

    print("[4/4] Saving Gaussian and metadata...")
    outputs["gaussian"][0].save_ply(str(ply_path))

    metadata = {
        "asset_name": "Nader Shah Afshar",
        "model_id": args.model_id,
        "prompt": prompt,
        "seed": args.seed,
        "texture_size": args.texture_size,
        "simplify": args.simplify,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": {"glb": glb_path.name, "gaussian_ply": ply_path.name},
    }
    metadata_path = args.output_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nGeneration completed.")
    print(f"Textured GLB: {glb_path.resolve()}")
    print(f"Gaussian PLY: {ply_path.resolve()}")
    print(f"Metadata:     {metadata_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nGeneration cancelled.", file=sys.stderr)
        raise SystemExit(130)
