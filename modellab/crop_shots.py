"""Crop capture shots around the character for close inspection."""
import sys

from PIL import Image

jobs = [
    # (src, box l,t,r,b as fractions, out)
    ("shots/v8_pause.png", (0.30, 0.15, 0.75, 0.75), "shots/v8_pause_crop.png"),
    ("shots/v8_strip_1.png", (0.15, 0.40, 0.55, 0.85), "shots/v8_strip1_crop.png"),
    ("shots/v8_strip_3.png", (0.30, 0.45, 0.70, 0.85), "shots/v8_strip3_crop.png"),
]
base = r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab"
for src, (l, t, r, b), out in jobs:
    im = Image.open(f"{base}/{src}")
    w, h = im.size
    crop = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    # upscale small crops so detail is visible
    scale = max(1, int(900 / crop.width))
    if scale > 1:
        crop = crop.resize((crop.width * scale, crop.height * scale), Image.LANCZOS)
    crop.save(f"{base}/{out}")
    print(f"saved {out} ({crop.width}x{crop.height})")
