"""Draw the section headings (hd-*.svg). Run: python scripts/make_headings.py"""
from pathlib import Path

from svgkit import W, svg, text

OUT = Path(__file__).resolve().parent.parent
HEADINGS = ["about", "stack", "projects", "stats", "about-this-page"]
SIZE = 18


def build(label):
    shown = label.replace("-", " ")
    adv = SIZE * 0.6
    x0 = 0
    prompt = text(x0, 26, ">", SIZE, "accent", 700)
    name = text(x0 + adv * 2, 26, shown, SIZE, "", 700)
    line_x = x0 + adv * (2 + len(shown) + 1)
    line = (
        f'<line x1="{line_x:.1f}" y1="20" x2="{W}" y2="20" '
        f'stroke="var(--faint)" stroke-width="1"/>'
    )
    return svg(W, 40, prompt + name + line, title=shown)


for h in HEADINGS:
    (OUT / f"hd-{h}.svg").write_text(build(h))
    print("wrote", f"hd-{h}.svg")
