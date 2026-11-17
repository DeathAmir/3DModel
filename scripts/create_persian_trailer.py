#!/usr/bin/env python3
import gc
import os
import subprocess
import urllib.request
from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "trailer"
SCENES_DIR = OUT / "scenes"
MODEL_ID = os.getenv("IMAGE_MODEL", "stabilityai/sd-turbo")
VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/fa/fa_IR/amir/medium/"
VOICE_MODEL = OUT / "fa_IR-amir-medium.onnx"
VOICE_CONFIG = OUT / "fa_IR-amir-medium.onnx.json"
NARRATION = "از دل تاریخ، نامی برخاست که مرزهای جهان را به لرزه انداخت. نادرشاه افشار؛ فرمانده‌ای که از آشوب، امپراتوری ساخت. در خیزش فرمانروایان، سپاه خود را گرد آورید، سرزمین‌ها را فتح کنید و برای شکوه ایران بجنگید. هر تصمیم، سرنوشت یک امپراتوری را تغییر می‌دهد. خیزش فرمانروایان؛ تاریخ را از نو بنویسید."
SCENES = [
    ("طلوع یک امپراتوری", "cinematic wide establishing shot of 18th century Persian empire at sunrise, Isfahan skyline, monumental Persian architecture, golden atmospheric light, historically inspired, detailed realistic epic strategy game concept art"),
    ("ظهور نادرشاه", "Nader Shah Afshar, powerful 18th century Persian king and military commander, historically inspired Afshar clothing, tall turban, thick dark beard and moustache, ornate Persian armor, standing beside a war horse, cinematic portrait, realistic epic game concept art"),
    ("سپاه افشاری", "vast disciplined 18th century Persian Afshar cavalry army riding across a rugged Iranian plateau, banners moving in the wind, dramatic dust, cinematic wide shot, historically inspired realistic strategy game art"),
    ("نبرد برای سرزمین‌ها", "epic historical battle scene between 18th century Persian armies on a vast mountain plain, cavalry formations, distant fortifications, dramatic cloudy sky, no modern objects, cinematic realistic game concept art"),
    ("گسترش قلمرو", "ornate antique parchment map of Persia and Central Asia on a royal strategy table, miniature golden army pieces, compass, candlelight, detailed historical cartography, cinematic top down view, realistic game art"),
    ("میراث فرمانروایان", "majestic Persian royal palace and monumental gate at golden sunset, Persian banners, distant army returning victorious, epic cinematic final shot, historically inspired 18th century Iran, realistic strategy game concept art"),
]

def run(args, **kwargs):
    subprocess.run(args, check=True, **kwargs)

def download(url, target, min_bytes=100_000):
    if target.exists() and target.stat().st_size > min_bytes:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "KheezeshTrailer/1.0"})
    with urllib.request.urlopen(request, timeout=240) as response, target.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
    if target.stat().st_size < min_bytes:
        raise RuntimeError(f"Downloaded model file looks incomplete: {target}")

def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def rtl(value):
    return get_display(arabic_reshaper.reshape(value))

def generate_scenes():
    torch.set_num_threads(max(1, min(6, os.cpu_count() or 2)))
    torch.set_grad_enabled(False)
    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, use_safetensors=True
    ).to("cpu")
    pipe.enable_attention_slicing()
    pipe.set_progress_bar_config(disable=False)
    generator = torch.Generator(device="cpu").manual_seed(20261117)
    for index, (caption, prompt) in enumerate(SCENES, 1):
        target = SCENES_DIR / f"scene-{index:02d}.png"
        if target.exists() and target.stat().st_size > 100_000:
            continue
        print(f"Generating AI scene {index}/{len(SCENES)}: {caption}", flush=True)
        result = pipe(
            prompt=prompt,
            negative_prompt="text, watermark, logo, modern buildings, modern vehicles, blurry, deformed face, extra limbs",
            width=384, height=384, num_inference_steps=1, guidance_scale=0.0,
            generator=generator,
        )
        result.images[0].save(target)
        del result
    del pipe
    gc.collect()

def make_overlay(index, caption):
    image = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1920, 210), fill=(9, 9, 13, 180))
    draw.rectangle((0, 1000, 1920, 1080), fill=(9, 9, 13, 165))
    draw.text((1810, 75), rtl("خیزش فرمانروایان"), font=font(76, True), fill=(244, 207, 139), anchor="ra")
    draw.text((1810, 160), rtl(caption), font=font(36), fill=(255, 244, 222), anchor="ra")
    draw.text((110, 1038), rtl("روایت سینمایی ساخته‌شده با هوش مصنوعی"), font=font(27), fill=(235, 218, 190), anchor="la")
    draw.text((1810, 1038), f"{index:02d} / {len(SCENES):02d}", font=font(28, True), fill=(244, 207, 139), anchor="ra")
    target = OUT / f"overlay-{index:02d}.png"
    image.save(target)
    return target

def render_video():
    clips = []
    for index, (caption, _) in enumerate(SCENES, 1):
        source = SCENES_DIR / f"scene-{index:02d}.png"
        overlay = make_overlay(index, caption)
        clip = OUT / f"clip-{index:02d}.mp4"
        filters = (
            "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            "zoompan=z='min(zoom+0.0008,1.08)':d=150:s=1920x1080:fps=30,format=yuv420p[bg];"
            "[1:v]format=rgba[ov];[bg][ov]overlay=0:0:shortest=1[v]"
        )
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(source), "-loop", "1", "-i", str(overlay),
             "-filter_complex", filters, "-map", "[v]", "-t", "5", "-an", "-r", "30",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p", str(clip)])
        clips.append(clip)
    listing = OUT / "clips.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips), encoding="utf-8")
    picture = OUT / "picture.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(picture)])
    return picture

def make_voice():
    download(VOICE_BASE + "fa_IR-amir-medium.onnx", VOICE_MODEL)
    download(VOICE_BASE + "fa_IR-amir-medium.onnx.json", VOICE_CONFIG, min_bytes=100)
    voice = OUT / "persian-narration.wav"
    run(["piper", "--model", str(VOICE_MODEL), "--config", str(VOICE_CONFIG),
         "--output_file", str(voice)], input=NARRATION.encode("utf-8"))
    return voice

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    generate_scenes()
    picture = render_video()
    voice = make_voice()
    final = OUT / "kheezesh-farmanravaan-trailer-fa.mp4"
    audio = (
        "[1:a]aresample=48000,volume=1.0[voice];"
        "sine=frequency=55:sample_rate=48000:duration=30,volume=0.035,lowpass=f=180[m1];"
        "sine=frequency=82.41:sample_rate=48000:duration=30,volume=0.018,lowpass=f=260[m2];"
        "[m1][m2]amix=inputs=2:duration=longest[ambient];"
        "[voice][ambient]amix=inputs=2:duration=longest:dropout_transition=2[a]"
    )
    run(["ffmpeg", "-y", "-i", str(picture), "-i", str(voice), "-filter_complex", audio,
         "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final)])
    print(f"Persian AI trailer created: {final}", flush=True)

if __name__ == "__main__":
    main()
