# Persian AI trailer (CPU + RAM)

This trailer is generated from scratch. It does not require gameplay recordings, a face-camera clip, an API key, CUDA, or an NVIDIA GPU.

## What it does

- Generates six cinematic Persian-history scenes with the local Stable Diffusion Turbo model.
- Forces inference onto the CPU and uses system RAM; CUDA is disabled in the workflow.
- Creates Persian right-to-left title cards and scene captions.
- Produces offline Persian neural narration with the Piper `fa_IR-amir-medium` voice.
- Adds quiet, procedurally synthesized cinematic ambience and renders a 1080p, 30 FPS MP4.

The video is explicitly presented as an AI-generated cinematic trailer, not as real gameplay footage.

## Run on GitHub

Open **Actions → Build Persian AI Trailer (CPU + RAM) → Run workflow**. No repository secrets are needed. The finished MP4, generated scene images, and narration are uploaded as the artifact:

`kheezesh-farmanravaan-persian-ai-trailer-cpu`

CPU generation is slow. The workflow allows up to six hours. The first run downloads the image model and Persian voice model.

## Run locally

Use Python 3.11, FFmpeg, and Persian Noto fonts. Install CPU-only PyTorch first, then dependencies:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-trailer-cpu.txt
```

Then run:

```bash
CUDA_VISIBLE_DEVICES="" python scripts/create_persian_trailer.py
```

Output:

`outputs/trailer/kheezesh-farmanravaan-trailer-fa.mp4`

Generated scene images and Persian narration are kept in `outputs/trailer/`.

## Models and licenses

- Image generation: `stabilityai/sd-turbo` from Hugging Face. Review its model card and license before redistribution.
- Persian narration: Piper `fa_IR-amir-medium` voice. Review the voice model card and license before redistribution.
