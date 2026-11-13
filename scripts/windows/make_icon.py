"""Generate the Windows application icon (.ico) used by the exe and the installer.

The design matches the tray icon: a blue calendar with a dark header.
Usage: python scripts/windows/make_icon.py <output.ico>
"""

import sys

from PIL import Image, ImageDraw

SIZES = [16, 24, 32, 48, 64, 128, 256]


def draw(size: int = 256) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    pad = size // 8
    header = pad + size // 5
    radius = max(1, size // 16)
    dc.rounded_rectangle(
        (pad, pad, size - pad, size - pad),
        radius,
        fill=(0, 120, 212),
        outline=(0, 0, 0),
    )
    dc.rounded_rectangle(
        (pad, pad, size - pad, header), radius, fill=(0, 80, 140), outline=(0, 0, 0)
    )
    # Two binder rings on the header.
    ring_w = max(1, size // 16)
    for x in (size // 3, 2 * size // 3):
        dc.rectangle(
            (x - ring_w // 2, pad - ring_w, x + ring_w // 2, pad + ring_w),
            fill=(0, 0, 0),
        )
    # A 3x2 grid of day cells.
    cell = (size - 2 * pad) // 5
    top = header + cell // 2
    for row in range(2):
        for col in range(3):
            x0 = pad + cell // 2 + col * (cell + cell // 2)
            y0 = top + row * (cell + cell // 3)
            dc.rectangle((x0, y0, x0 + cell, y0 + cell * 2 // 3), fill=(255, 255, 255))
    return image


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    draw().save(sys.argv[1], format="ICO", sizes=[(s, s) for s in SIZES])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
