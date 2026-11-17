#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://api.meshy.ai"
KEY = os.environ.get("MESHY_API_KEY")
OUT = Path("outputs/nader_shah_afshar")
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = """Create a historically grounded, full-body 3D game character representing Nader Shah Afshar (Nader Qoli Beg), the famous 18th-century Afsharid Shah of Persia, not a generic fantasy king. A mature Persian military ruler with a recognizable stern historical-warrior presence, strong nose, thick dark moustache and beard, wearing authentic 18th-century Afsharid Persian royal military clothing: layered deep crimson and dark teal coat, detailed woven fabric, gold embroidery, broad sash, leather belt, historically plausible Persian armor accents, tall boots, and a Persian turban with a restrained jeweled aigrette. Full figure, head to toe, feet visible, centered, neutral A-pose suitable for game rigging, anatomically correct human body, realistic face and hands, individual fingers, detailed fabric folds, metal, leather and embroidery. Premium realistic historical strategy game asset, physically based materials, clean silhouette, no fantasy horns, no modern objects, no extra limbs, no text, no watermark."""
TEXTURE_PROMPT = "Historically plausible 18th-century Afsharid Persian royal military attire. Realistic woven crimson and deep teal fabric, intricate gold thread embroidery, aged polished steel and brass, natural leather, realistic skin, detailed moustache and beard. PBR base color, metallic, roughness and normal detail. No painted studio shadows."

def call(path, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(BASE + path, data=data, method=method, headers={
        "Authorization": "Bearer " + KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    with urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode())

def wait_task(task_id, label):
    deadline = time.time() + 60 * 90
    while time.time() < deadline:
        task = call("/openapi/v2/text-to-3d/" + task_id)
        status = task.get("status")
        print(f"{label}: {status} ({task.get('progress', 0)}%)", flush=True)
        if status == "SUCCEEDED":
            return task
        if status in ("FAILED", "CANCELED", "EXPIRED"):
            raise RuntimeError(f"{label} failed: {task.get('task_error')}")
        time.sleep(20)
    raise TimeoutError(f"{label} timed out after 90 minutes")

def download(url, path):
    req = Request(url, headers={"User-Agent": "KheezeshFarmanravaanAssetPipeline/1.0"})
    with urlopen(req, timeout=180) as response, open(path, "wb") as target:
        target.write(response.read())

def main():
    if not KEY:
        raise SystemExit("Missing MESHY_API_KEY repository secret. Add it in Settings > Secrets and variables > Actions.")
    prompt = os.environ.get("MODEL_PROMPT", PROMPT)[:800]
    model = os.environ.get("MESHY_MODEL", "latest")
    geometry = os.environ.get("GEOMETRY_RESOLUTION", "standard")
    texture = os.environ.get("TEXTURE_RESOLUTION", "4k")
    preview_payload = {
        "mode": "preview",
        "prompt": prompt,
        "ai_model": model,
        "geometry_resolution": geometry,
        "should_remesh": False,
        "pose_mode": "a-pose",
        "target_formats": ["glb"],
        "moderation": True
    }
    print("Creating Meshy preview task...", flush=True)
    preview_id = call("/openapi/v2/text-to-3d", "POST", preview_payload)["result"]
    preview = wait_task(preview_id, "Geometry")
    refine_payload = {
        "mode": "refine",
        "preview_task_id": preview_id,
        "enable_pbr": True,
        "texture_resolution": texture,
        "ai_model": model,
        "texture_prompt": TEXTURE_PROMPT,
        "target_formats": ["glb"]
    }
    print("Creating PBR texture refinement task...", flush=True)
    refine_id = call("/openapi/v2/text-to-3d", "POST", refine_payload)["result"]
    final = wait_task(refine_id, "Texturing")
    urls = final.get("model_urls") or {}
    glb_url = urls.get("glb")
    if not glb_url:
        raise RuntimeError("Meshy task succeeded but did not return a GLB URL.")
    download(glb_url, OUT / "nader_shah_afshar.glb")
    for index, maps in enumerate(final.get("texture_urls") or []):
        for name, url in maps.items():
            if url:
                download(url, OUT / f"texture_{index}_{name}.png")
    if final.get("thumbnail_url"):
        download(final["thumbnail_url"], OUT / "model-preview.png")
    metadata = {
        "title_fa": "نادرشاه افشار",
        "game_title_fa": "خیزش فرمانروایان",
        "provider": "Meshy API",
        "model": model,
        "preview_task_id": preview_id,
        "refine_task_id": refine_id,
        "prompt": prompt,
        "texture_prompt": TEXTURE_PROMPT,
        "geometry_resolution": geometry,
        "texture_resolution": texture,
        "pbr_enabled": True,
        "preview_status": preview.get("status"),
        "final_status": final.get("status"),
        "model_urls": urls,
        "texture_urls": final.get("texture_urls", [])
    }
    (OUT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Textured Nader Shah GLB and PBR maps saved to outputs/nader_shah_afshar", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise