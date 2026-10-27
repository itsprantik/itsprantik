"""Shared helpers for the generated SVGs on this profile.

Everything is drawn locally, so nothing loads from a third-party server.
Text positions are set explicitly (x/y per element or textLength per row), so the
layout does not depend on which monospace font the viewer has installed.
"""
from xml.sax.saxutils import escape

W = 620

CSS = """
:root{--fg:#1f2328;--dim:#656d76;--faint:#d0d7de;--accent:#0969da}
@media (prefers-color-scheme: dark){
  :root{--fg:#e6edf3;--dim:#8b949e;--faint:#30363d;--accent:#58a6ff}
}
text{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;fill:var(--fg)}
.dim{fill:var(--dim)}
.accent{fill:var(--accent)}
.faint{fill:var(--faint)}
"""


def svg(w, h, body, title=""):
    t = f"<title>{escape(title)}</title>" if title else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img">{t}<style>{CSS}</style>{body}</svg>\n'
    )


def fade(delay=0.0, dur=0.6):
    """SMIL fade-in. GitHub strips scripts, but SMIL inside an <img> SVG still runs."""
    return (
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" '
        f'dur="{dur}s" fill="freeze"/>'
    )


def text(x, y, s, size=12, cls="", weight=400, anchor="start", extra=""):
    c = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}"{c} {extra}>{escape(str(s))}</text>'
    )
