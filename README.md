# خیزش فرمانروایان | Kheezesh-e Farmanravaan

Asset-generation workspace for the Persian historical strategy game **خیزش فرمانروایان**.

## Persian loading screen

Open [game/loading/index.html](game/loading/index.html) in a browser to preview the responsive Persian RTL loading screen. It uses Vazirmatn, supports Persian text, and includes animated loading status and a historical gold/dark visual theme. It is a standalone HTML screen that can be embedded in a web-based loading surface or used as a design reference for a native game UI.

## Nader Shah Afshar — textured 3D character

The previous CPU-only Shap-E pipeline was removed because its output quality was not suitable for a recognizable historical human character.

The new workflow uses the official Meshy Text-to-3D API in two stages:
1. Generate the character's geometry in a neutral A-pose.
2. Refine the mesh with 4K PBR texturing and export a GLB.

The prompt describes **Nader Shah Afshar**, the 18th-century Afsharid ruler of Persia, with historically inspired Persian military clothing, turban, moustache and beard. The generated result is an AI interpretation, not a guaranteed exact reconstruction of his face. For stronger likeness, provide a good full-body reference image and use an image-to-3D workflow.

### Configure the API key

Create a Meshy API key and add it to the repository as an Actions secret named:

`MESHY_API_KEY`

Meshy API task creation requires an eligible paid plan and sufficient credits. The workflow does not store the key in the repository.

### Run

1. Open **Actions**.
2. Select **Generate Nader Shah Afshar (Meshy AI)**.
3. Choose texture resolution (4K recommended) and geometry detail.
4. Select **Run workflow**.

Workflow file: `.github/workflows/generate-meshy.yml`

The generated artifact contains:
- `nader_shah_afshar.glb` — textured 3D model.
- `texture_*_base_color.png`, `texture_*_metallic.png`, `texture_*_roughness.png`, `texture_*_normal.png` — maps returned by Meshy.
- `model-preview.png` — preview image, when returned by the API.
- `metadata.json` — generation settings and task identifiers.

The model is uploaded as a GitHub Actions artifact; large generated assets are not committed to Git.

## Persian AI trailer (CPU + RAM)

The trailer is now generated entirely from AI-created historical scenes; it does not depend on gameplay footage, a face-camera recording, a cloud API key, CUDA, or an NVIDIA GPU.

- Image model: Stable Diffusion Turbo, executed on CPU using system RAM.
- Persian voice: offline Piper neural TTS (`fa_IR-amir-medium`).
- Output: cinematic 1080p / 30 FPS MP4 with Persian RTL titles and generated ambient soundtrack.
- Workflow: [`.github/workflows/build-persian-trailer.yml`](.github/workflows/build-persian-trailer.yml).
- Output artifact: `kheezesh-farmanravaan-persian-ai-trailer-cpu`.

The result is clearly labelled as an AI-generated cinematic trailer, not real gameplay. Open **Actions → Build Persian AI Trailer (CPU + RAM)** to view the run and download its MP4 artifact.

## References

- [Meshy Text-to-3D API](https://docs.meshy.ai/en/api/text-to-3d)
- [Meshy Image-to-3D API](https://docs.meshy.ai/en/api/image-to-3d)
- [Meshy API pricing and access](https://www.meshy.ai/api)
