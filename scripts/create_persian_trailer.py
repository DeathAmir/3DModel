#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "trailer"
OUTPUT = OUT / "kheezesh-farmanravaan-trailer-en.mp4"
API = "https://api.replicate.com/v1"
MODEL = "wan-video/wan-2.7-t2v"
TOKEN = os.environ.get("REPLICATE_API_TOKEN", "").strip()

PROMPT = os.environ.get("VIDEO_PROMPT") or (
    "A breathtaking, historically inspired cinematic trailer set in 18th-century Persia during the rise of Nader Shah Afshar. "
    "Open with an immense aerial view over Isfahan at sunrise, golden light spilling across Persian domes and gardens. "
    "A powerful Persian commander inspired by Nader Shah, wearing authentic-looking Afshar-era robes, armor and a tall turban, "
    "stands beside his warhorse as banners move in the wind. Transition naturally into disciplined Persian cavalry riding "
    "across a vast rugged plateau, then a large-scale historical battle with cavalry formations, distant fortresses, dust, "
    "and dramatic weather. End with a majestic Persian royal palace and the army returning beneath a glowing sunset. "
    "Ultra cinematic historical realism, physically believable movement, detailed costumes and architecture, sweeping crane "
    "shots, aerial tracking shots, dramatic but natural lighting, coherent visual continuity, premium AAA historical strategy "
    "game announcement trailer, widescreen 16:9. No modern objects, no fantasy monsters, no guns, no text, no subtitles, "
    "no logos, no watermarks. Generate fitting cinematic orchestral ambience and environmental battle sounds."
)
NEGATIVE = (
    "low resolution, blurry, flicker, jitter, distorted anatomy, extra limbs, duplicated people, "
    "floating objects, modern buildings, modern weapons, modern vehicles, text, subtitles, logo, watermark"
)

def request_json(url, method="GET", payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "KheezeshFarmanravaanTrailer/2.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Replicate API returned HTTP {exc.code}: {detail}") from exc

def create_prediction():
    print("Submitting a 15-second Wan 2.7 text-to-video request...", flush=True)
    return request_json(
        f"{API}/models/{MODEL}/predictions",
        method="POST",
        payload={
            "input": {
                "prompt": PROMPT,
                "negative_prompt": NEGATIVE,
                "duration": 15,
                "resolution": "1080p",
                "aspect_ratio": "16:9",
                "enable_prompt_expansion": True,
            }
        },
    )

def wait_for_prediction(prediction):
    prediction_id = prediction.get("id")
    poll_url = prediction.get("urls", {}).get("get")
    if not prediction_id or not poll_url:
        raise RuntimeError(f"Replicate did not return a prediction ID: {prediction}")
    deadline = time.monotonic() + 5400
    while time.monotonic() < deadline:
        status = prediction.get("status")
        print(f"Video generation status: {status}", flush=True)
        if status == "succeeded":
            output = prediction.get("output")
            if isinstance(output, list):
                output = output[0] if output else None
            if not isinstance(output, str) or not output.startswith("https://"):
                raise RuntimeError(f"Unexpected video output: {output}")
            return output
        if status in ("failed", "canceled"):
            raise RuntimeError(f"Video generation {status}: {prediction.get('error')}")
        time.sleep(10)
        prediction = request_json(poll_url)
    raise TimeoutError("Video generation exceeded the 90-minute workflow limit.")

def download_video(url):
    OUT.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "KheezeshFarmanravaanTrailer/2.0"})
    temporary = OUTPUT.with_suffix(".mp4.part")
    print("Downloading generated MP4...", flush=True)
    with urllib.request.urlopen(req, timeout=300) as response, temporary.open("wb") as target:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)
    if not temporary.exists() or temporary.stat().st_size < 100_000:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("The generated MP4 is missing or unexpectedly small.")
    temporary.replace(OUTPUT)
    print(f"AI video created: {OUTPUT}", flush=True)
    print(f"File size: {OUTPUT.stat().st_size / (1024 * 1024):.2f} MB", flush=True)

def main():
    if not TOKEN:
        print(
            "Missing GitHub Actions secret REPLICATE_API_TOKEN. "
            "Create a Replicate API token and add it under Settings > Secrets and variables > Actions.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    prediction = create_prediction()
    video_url = wait_for_prediction(prediction)
    download_video(video_url)

if __name__ == "__main__":
    main()
