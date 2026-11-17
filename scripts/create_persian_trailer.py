#!/usr/bin/env python3
import asyncio
import os
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(".")
GAMEPLAY = ROOT / "assets" / "trailer" / "gameplay.mp4"
CAMERA = ROOT / "assets" / "trailer" / "player-camera.mp4"
OUT = ROOT / "outputs" / "trailer"
OUT.mkdir(parents=True, exist_ok=True)
VOICE = os.getenv("PERSIAN_VOICE", "fa-IR-FaridNeural")
TEXT = "به خیزش فرمانروایان خوش آمدید! در این بازی، سرنوشت امپراتوری‌ها در دستان شماست. سرزمین‌های تازه را فتح کنید، ارتش خود را فرماندهی کنید و تاریخ را از نو بنویسید. خیزش فرمانروایان؛ فرمانروایی از آنِ شماست."

def run(args):
    subprocess.run(args, check=True)

async def make_voice():
    tts = edge_tts.Communicate(TEXT, VOICE, rate="-3%", pitch="-1Hz")
    await tts.save(str(OUT / "persian-narration.mp3"))

def title_card():
    w, h = 1920, 220
    image = Image.new("RGBA", (w, h), (12, 10, 8, 210))
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
    if not Path(font_path).exists():
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 72)
    title = get_display(arabic_reshaper.reshape("خیزش فرمانروایان"))
    subtitle = get_display(arabic_reshaper.reshape("تاریخ را از نو بنویس"))
    draw.text((w // 2, 70), title, font=font, fill=(239, 205, 137), anchor="mm", direction="rtl")
    small = ImageFont.truetype(font_path, 34)
    draw.text((w // 2, 158), subtitle, font=small, fill=(240, 230, 210), anchor="mm", direction="rtl")
    image.save(OUT / "title-overlay.png")

def main():
    if not GAMEPLAY.is_file():
        raise SystemExit("Missing assets/trailer/gameplay.mp4. Add a real gameplay capture before running the trailer workflow.")
    if not CAMERA.is_file():
        raise SystemExit("Missing assets/trailer/player-camera.mp4. Add a clip showing the person playing the game.")
    asyncio.run(make_voice())
    title_card()
    # Loop the gameplay and face-camera clips so the complete Persian narration is covered.
    args = [
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(GAMEPLAY),
        "-stream_loop", "-1", "-i", str(CAMERA),
        "-i", str(OUT / "title-overlay.png"),
        "-i", str(OUT / "persian-narration.mp3"),
        "-filter_complex",
        "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2[game];"
        "[1:v]scale=480:-1,setsar=1[cam];"
        "[game][cam]overlay=W-w-48:48[withcam];"
        "[2:v]format=rgba[title];[withcam][title]overlay=0:0:eof_action=repeat[v]",
        "-map", "[v]", "-map", "3:a:0", "-c:v", "libx264", "-preset", "medium",
        "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(OUT / "kheezesh-farmanravaan-trailer-fa.mp4")
    ]
    run(args)
    print("Trailer created:", OUT / "kheezesh-farmanravaan-trailer-fa.mp4")

if __name__ == "__main__":
    main()
