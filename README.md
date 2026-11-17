# 3DModel — Text-to-3D Game Asset Generator

A prompt-driven 3D asset workflow powered by Microsoft's **TRELLIS Text Large**. On first run, the pipeline downloads the model from Hugging Face into its local cache, generates a 3D representation, extracts a textured GLB, and saves the result under `outputs/`.

## Model

- Hugging Face: [microsoft/TRELLIS-text-large](https://huggingface.co/microsoft/TRELLIS-text-large)
- TRELLIS Text Large: 1.1B parameters; model repository is about 2.28 GB at the time of writing.
- License: MIT (model card).
- Output: textured GLB plus Gaussian PLY.
- Default texture extraction: 2048 px.

TRELLIS's own authors note that text-conditioned results are less creative and detailed than image-conditioned generation. This repository uses the direct text pipeline to keep the workflow prompt-only. Full-body human characters are a difficult prompt category, so try multiple seeds and inspect the output before using it in a game.

## Hardware requirements

The official TRELLIS project is tested on Linux and requires an NVIDIA CUDA GPU with at least 16 GB VRAM. 24 GB+ is recommended for more headroom. It is not a CPU-only workflow.

An AMD Radeon RX 580 does not provide the CUDA runtime required by this setup. Use a compatible Linux machine or cloud VM with an NVIDIA GPU. The model weights are cached by Hugging Face and are deliberately not committed to this Git repository.

## Install

Follow the upstream installation steps because TRELLIS uses compiled CUDA extensions that must match the installed PyTorch/CUDA version:

```bash
git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git
cd TRELLIS
. ./setup.sh --new-env --basic --xformers --flash-attn --spconv --mipgaussian --kaolin --nvdiffrast
conda activate trellis
```

Clone this project in a separate directory:

```bash
git clone https://github.com/DeathAmir/3DModel.git
cd 3DModel
pip install -r requirements.txt
```

If TRELLIS is not located at `../TRELLIS`, set its path:

```bash
export TRELLIS_ROOT=/absolute/path/to/TRELLIS
```

## Generate Nader Shah Afshar

```bash
python generate.py --prompt-file prompts/nader_shah_afshar.txt --seed 42 --texture-size 2048
```

Or pass a custom English prompt:

```bash
python generate.py --prompt "A stylized full-body Persian royal warrior..." --seed 7
```

The first run downloads `microsoft/TRELLIS-text-large` into the Hugging Face cache. Set `HF_HOME` to change the cache location:

```bash
export HF_HOME=/path/to/huggingface-cache
```

Generated files:

- `outputs/nader_shah_afshar/nader_shah_afshar.glb` — textured mesh.
- `outputs/nader_shah_afshar/nader_shah_afshar.ply` — Gaussian representation.
- `outputs/nader_shah_afshar/metadata.json` — prompt, model, seed, and export settings.

Import the GLB into Blender using **File → Import → glTF 2.0**. Check topology, UVs, scale, materials, and silhouette before production use. The pipeline does not rig or animate the character.

## Options

Run `python generate.py --help` for all options:

- `--model-id`: Hugging Face model ID (default: `microsoft/TRELLIS-text-large`).
- `--seed`: reproducible generation seed.
- `--texture-size`: texture resolution (512–4096, default 2048).
- `--simplify`: mesh simplification ratio (default 0.95).
- `--output-dir`: output directory.

## References

- [Microsoft TRELLIS source and installation](https://github.com/microsoft/TRELLIS)
- [TRELLIS Text Large on Hugging Face](https://huggingface.co/microsoft/TRELLIS-text-large)
- [TRELLIS paper](https://arxiv.org/abs/2412.01506)

TRELLIS is an upstream project by Microsoft Research. This repository is an integration workflow and is not affiliated with Microsoft.
