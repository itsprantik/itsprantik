"""Turn a photo (or your name) into the ASCII portrait, ascii.svg.

  python scripts/make_portrait.py path/to/photo.jpg      # your face
  python scripts/make_portrait.py --name prantik         # placeholder wordmark

Needs Pillow:  pip install pillow
Each row is one <text> element with an explicit textLength, so every character
lands on a fixed grid whatever monospace font the viewer has.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from xml.sax.saxutils import escape

RAMP = " .:+#@"  # quiet -> loud
OUT = Path(__file__).resolve().parent.parent / "ascii.svg"
ADV = 0.6  # advance width of a monospace char, in em
LINE = 1.2  # row pitch, in em


def from_photo(path, cols):
    im = ImageOps.exif_transpose(Image.open(path)).convert("L")
    im = ImageOps.autocontrast(im, cutoff=2)
    rows = round(im.height / im.width * cols * ADV / LINE)
    return im.resize((cols, rows), Image.LANCZOS)


def from_name(name, cols):
    font = ImageFont.load_default(size=120)
    box = font.getbbox(name)
    w, h = box[2] - box[0] + 40, box[3] - box[1] + 40
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((20 - box[0], 20 - box[1]), name, fill=255, font=font)
    rows = max(1, round(h / w * cols * ADV / LINE))
    return im.resize((cols, rows), Image.LANCZOS)


def to_svg(im, invert, fs=10.0):
    cols, rows = im.size
    px = im.load()
    body = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            v = px[c, r] / 255
            if invert:
                v = 1 - v
            line += RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
        y = (r + 1) * fs * LINE
        body.append(
            f'<text x="0" y="{y:.1f}" textLength="{cols * fs * ADV:.1f}" '
            f'lengthAdjust="spacing" xml:space="preserve">{escape(line)}</text>'
        )
    w, h = cols * fs * ADV, rows * fs * LINE + fs * 0.4
    css = (
        "text{font-family:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;"
        f"font-size:{fs}px;fill:#1f2328;white-space:pre}}"
        "@media (prefers-color-scheme: dark){text{fill:#e6edf3}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.1f} {h:.1f}" role="img"><title>Prantik Mandal</title>'
        f"<style>{css}</style>{''.join(body)}</svg>\n"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("photo", nargs="?")
    ap.add_argument("--name")
    ap.add_argument("--cols", type=int, default=74)
    a = ap.parse_args()
    if a.name:
        im, invert = from_name(a.name, a.cols), False
    elif a.photo:
        # dark pixels draw loud characters so the face reads on a light page
        im, invert = from_photo(a.photo, a.cols), True
    else:
        ap.error("give a photo path or --name")
    OUT.write_text(to_svg(im, invert))
    print("wrote", OUT)
