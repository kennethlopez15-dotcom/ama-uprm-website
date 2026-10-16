"""Generate interior photo variants. Requires Pillow; no site runtime dependency.

Run: python scripts/responsive_images.py
Original JPEGs remain the fallback. Never upscale an original.
"""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = ('about-hero-real', 'event-real-meeting', 'event-real-wide')


def variants(width):
    return sorted({min(width, size) for size in (480, 960, 1440)})


if __name__ == '__main__':
    for name in PHOTOS:
        source = ROOT / 'assets' / 'img' / (name + '.jpg')
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')
            for width in variants(image.width):
                height = round(image.height * width / image.width)
                target = source.with_name(f'{name}-{width}.webp')
                image.resize((width, height), Image.Resampling.LANCZOS).save(target, 'WEBP', quality=82, method=6)
                print(f'{target.name}: {width}x{height}, {target.stat().st_size} bytes')
