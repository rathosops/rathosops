"""Reusable SVG building blocks for the retro / low-poly profile assets.

This module is the single source of truth for the visual language: the
vaporwave palette, small primitive helpers (escaping, document wrapper,
gradients, panels, text, pixel bars) and the procedural low-poly generators
(deterministic value noise, faceted sun, triangulated terrain).

Every renderer in :mod:`gen_profile` composes these primitives, so styling
changes live in one place (DRY). Helpers return SVG strings and never perform
I/O, which keeps them trivially testable (KISS).
"""
from __future__ import annotations

import math
from typing import Callable, Iterable

# ── vaporwave palette (shared by every asset, incl. assets/header.svg) ───────
BG = "#1a0b2e"
BG2 = "#241046"
PINK = "#ff2e97"
PINK2 = "#ff6bd6"
PURPLE = "#bf00ff"
CYAN = "#00ffff"
TEXT = "#e0c3fc"
INDIGO = "#3a0ca3"
DIM = "#2a1a44"

#: Low → high colour ramp used for height/intensity shading.
HEIGHT_RAMP = [(0.0, INDIGO), (0.45, PURPLE), (0.75, PINK), (1.0, CYAN)]

MONO = "monospace"
PIXEL = "'Press Start 2P', monospace"


# ── colour helpers ───────────────────────────────────────────────────────────
def lerp(color_a: str, color_b: str, t: float) -> str:
    """Linearly interpolate two ``#rrggbb`` colours, ``t`` in ``[0, 1]``."""
    a, b = color_a.lstrip("#"), color_b.lstrip("#")
    channels = (
        round(int(a[i : i + 2], 16) + (int(b[i : i + 2], 16) - int(a[i : i + 2], 16)) * t)
        for i in (0, 2, 4)
    )
    return "#" + "".join(f"{c:02x}" for c in channels)


def ramp(t: float, stops: list[tuple[float, str]] = HEIGHT_RAMP) -> str:
    """Sample a colour ramp at ``t`` in ``[0, 1]`` (stops sorted by position)."""
    t = max(0.0, min(1.0, t))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            span = p1 - p0
            return lerp(c0, c1, (t - p0) / span if span else 0.0)
    return stops[-1][1]


# ── text / document helpers ───────────────────────────────────────────────────
def esc(value: object) -> str:
    """Escape a value for safe inclusion in SVG text/attributes."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def document(width: float, height: float, *body: str, label: str = "") -> str:
    """Wrap ``body`` fragments in a sized, accessible ``<svg>`` root element."""
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(label)}">'
        + "".join(body)
        + "</svg>\n"
    )


def text(x: float, y: float, content: str, *, size: float = 13, fill: str = TEXT,
         font: str = MONO, anchor: str = "start", weight: int = 400,
         spacing: float = 0) -> str:
    """Render a single ``<text>`` line (content is pre-escaped by the caller)."""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}>{content}</text>'
    )


# ── gradients / panels ────────────────────────────────────────────────────────
def linear_gradient(gid: str, stops: list[tuple[float, str]],
                    x2: float = 1, y2: float = 0) -> str:
    """A ``<linearGradient>`` def; direction defaults to horizontal."""
    body = "".join(f'<stop offset="{p*100:.0f}%" stop-color="{c}"/>' for p, c in stops)
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{body}</linearGradient>'


#: Gradient defs every card shares (title text + neon frame + panel fill).
SHARED_DEFS = (
    "<defs>"
    + linear_gradient("title", [(0, PINK2), (1, CYAN)])
    + linear_gradient("frame", [(0, PINK2), (0.5, PURPLE), (1, CYAN)], x2=1, y2=1)
    + linear_gradient("panel", [(0, BG2), (1, BG)], x2=0, y2=1)
    + "</defs>"
)


def scanline(width: float, height: float) -> str:
    """A faint cyan bar that sweeps top-to-bottom for a CRT feel."""
    return (
        f'<rect x="0" y="0" width="{width}" height="2.5" fill="{CYAN}" opacity="0.08">'
        f'<animate attributeName="y" values="-3;{height}" dur="5s" repeatCount="indefinite"/></rect>'
    )


def panel(width: float, height: float, title: str) -> str:
    """Bordered panel with neon frame, sweeping scanline and a title bar."""
    return (
        SHARED_DEFS
        + f'<rect x="0.75" y="0.75" width="{width-1.5}" height="{height-1.5}" rx="10" '
        f'fill="url(#panel)" stroke="url(#frame)" stroke-width="1.5"/>'
        + scanline(width, height)
        + text(18, 30, "&#9656; " + esc(title), size=13, fill="url(#title)", font=PIXEL)
        + f'<line x1="18" y1="40" x2="{width-18}" y2="40" stroke="{PURPLE}" '
        f'stroke-width="1" opacity="0.4"/>'
    )


# ── terminal window chrome ────────────────────────────────────────────────────
LINE_HEIGHT = 18  #: vertical advance between monospace rows
BODY_TOP = 62     #: y of the first body row (below the title bar)


def window(width: float, title: str, body: str, *, rows: int,
           decoration: str = "", label: str = "") -> str:
    """A retro terminal window: traffic lights, title bar, neon frame, body.

    ``rows`` is the number of monospace rows in ``body`` and drives the height
    so every terminal block shares identical chrome and spacing (DRY).
    ``decoration`` is optional extra SVG (e.g. a low-poly icon) drawn top-right.
    """
    height = BODY_TOP + rows * LINE_HEIGHT + 12
    dots = "".join(
        f'<circle cx="{20 + i*18}" cy="22" r="5.5" fill="{c}"/>'
        for i, c in enumerate((PINK, PURPLE, CYAN))
    )
    return document(
        width, height,
        SHARED_DEFS,
        f'<rect x="0.75" y="0.75" width="{width-1.5}" height="{height-1.5}" rx="10" '
        f'fill="url(#panel)" stroke="url(#frame)" stroke-width="1.5"/>',
        scanline(width, height),
        dots,
        text(width / 2, 27, esc(title), size=11, fill=PINK2, font=PIXEL, anchor="middle"),
        f'<line x1="12" y1="40" x2="{width-12}" y2="40" stroke="{PURPLE}" stroke-width="1" opacity="0.35"/>',
        decoration,
        body,
        label=label or title,
    )


def mono_rows(rows: list, *, x: float = 22, y0: float = BODY_TOP,
              size: float = 13) -> str:
    """Render monospace rows. Each row is a string or a list of ``(text, fill)``.

    Spaces are preserved (``xml:space``) so ASCII art and columns stay aligned.
    """
    out = []
    for i, row in enumerate(rows):
        y = y0 + i * LINE_HEIGHT
        spans = [(row, TEXT)] if isinstance(row, str) else row
        body = "".join(
            f'<tspan fill="{fill}" xml:space="preserve">{esc(seg)}</tspan>' for seg, fill in spans
        )
        out.append(
            f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
            f'xml:space="preserve">{body}</text>'
        )
    return "".join(out)


# ── low-poly decorative icons (vaporwave 3-D vibe) ───────────────────────────
def icon_crt(x: float, y: float, s: float = 1.0) -> str:
    """A faceted CRT computer/monitor in perspective."""
    def p(px, py):
        return f"{x+px*s:.1f},{y+py*s:.1f}"
    return (
        f'<g opacity="0.95">'
        f'<polygon points="{p(0,0)} {p(34,4)} {p(34,26)} {p(0,30)}" fill="{INDIGO}" stroke="{CYAN}" stroke-width="1"/>'
        f'<polygon points="{p(4,5)} {p(30,8)} {p(30,23)} {p(4,26)}" fill="{PURPLE}" opacity="0.7"/>'
        f'<polygon points="{p(4,5)} {p(17,6.5)} {p(17,25)} {p(4,26)}" fill="{PINK}" opacity="0.45"/>'
        f'<polygon points="{p(12,30)} {p(22,30)} {p(24,36)} {p(10,36)}" fill="{INDIGO}" stroke="{CYAN}" stroke-width="1"/>'
        f'</g>'
    )


def icon_gamepad(x: float, y: float, s: float = 1.0) -> str:
    """A low-poly retro game controller."""
    def p(px, py):
        return f"{x+px*s:.1f},{y+py*s:.1f}"
    return (
        f'<g opacity="0.95">'
        f'<polygon points="{p(2,4)} {p(34,4)} {p(40,18)} {p(26,18)} {p(18,12)} {p(10,18)} {p(-4,18)}" '
        f'fill="{PURPLE}" stroke="{CYAN}" stroke-width="1"/>'
        f'<rect x="{x+6*s:.1f}" y="{y+8*s:.1f}" width="{2.5*s:.1f}" height="{6*s:.1f}" fill="{CYAN}"/>'
        f'<rect x="{x+4*s:.1f}" y="{y+10*s:.1f}" width="{6.5*s:.1f}" height="{2.5*s:.1f}" fill="{CYAN}"/>'
        f'<circle cx="{x+28*s:.1f}" cy="{y+9*s:.1f}" r="{1.8*s:.1f}" fill="{PINK}"/>'
        f'<circle cx="{x+32*s:.1f}" cy="{y+12*s:.1f}" r="{1.8*s:.1f}" fill="{PINK2}"/>'
        f'</g>'
    )


def icon_pizza(x: float, y: float, s: float = 1.0) -> str:
    """A faceted pizza slice with pepperoni."""
    def p(px, py):
        return f"{x+px*s:.1f},{y+py*s:.1f}"
    return (
        f'<g opacity="0.95">'
        f'<polygon points="{p(16,0)} {p(32,34)} {p(0,34)}" fill="#ffd36a" stroke="{PINK}" stroke-width="1"/>'
        f'<polygon points="{p(16,0)} {p(24,17)} {p(8,17)}" fill="#ffe066" opacity="0.8"/>'
        f'<polygon points="{p(16,0)} {p(6,21)} {p(0,34)} {p(0,34)}" fill="#ff9f78" opacity="0.5"/>'
        f'<circle cx="{x+13*s:.1f}" cy="{y+16*s:.1f}" r="{2.4*s:.1f}" fill="{PINK}"/>'
        f'<circle cx="{x+20*s:.1f}" cy="{y+24*s:.1f}" r="{2.4*s:.1f}" fill="{PINK}"/>'
        f'<circle cx="{x+10*s:.1f}" cy="{y+27*s:.1f}" r="{2*s:.1f}" fill="{PINK}"/>'
        f'</g>'
    )


# ── retro game widgets ────────────────────────────────────────────────────────
def pixel_bar(x: float, y: float, width: float, height: float, frac: float, *,
              segments: int = 20, color: str = CYAN, gap: float = 2) -> str:
    """A segmented 8-bit style progress bar filled to ``frac`` (``0..1``)."""
    frac = max(0.0, min(1.0, frac))
    seg_w = (width - gap * (segments - 1)) / segments
    filled = round(frac * segments)
    cells = []
    for i in range(segments):
        cx = x + i * (seg_w + gap)
        on = i < filled
        cells.append(
            f'<rect x="{cx:.1f}" y="{y}" width="{seg_w:.1f}" height="{height}" rx="1" '
            f'fill="{color if on else DIM}" opacity="{1 if on else 0.6}"/>'
        )
    return "".join(cells)


# ── procedural low-poly generators ───────────────────────────────────────────
def value_noise(seed: int = 0) -> Callable[[float], float]:
    """Return a smooth, deterministic 1-D noise function ``f(x) -> [0, 1]``.

    Uses hashed lattice points with smoothstep interpolation — no third-party
    dependency, identical output across runs for a given ``seed``.
    """
    def _hash(i: int) -> float:
        v = math.sin((i + seed * 57.0) * 12.9898) * 43758.5453
        return v - math.floor(v)

    def noise(x: float) -> float:
        i = math.floor(x)
        f = x - i
        u = f * f * (3 - 2 * f)  # smoothstep
        return _hash(i) * (1 - u) + _hash(i + 1) * u

    return noise


def faceted_sun(cx: float, cy: float, r: float, *, wedges: int = 18,
                bars: int = 6) -> str:
    """A low-poly sun: a triangle fan shaded by height, cut by retrowave bars."""
    tris = []
    for i in range(wedges):
        a0 = math.pi + i * math.pi / wedges          # upper semicircle only
        a1 = math.pi + (i + 1) * math.pi / wedges
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        shade = 1 - (abs((y0 + y1) / 2 - (cy - r)) / r)  # brighter near the top
        tris.append(
            f'<polygon points="{cx:.1f},{cy:.1f} {x0:.1f},{y0:.1f} {x1:.1f},{y1:.1f}" '
            f'fill="{ramp(shade, [(0, PURPLE), (0.5, PINK), (1, "#ffe066")])}"/>'
        )
    # retrowave horizontal cuts through the lower half of the disc
    cuts = []
    for i in range(bars):
        by = cy - i * (r / (bars + 1)) * 0.7
        cuts.append(
            f'<rect x="{cx-r}" y="{by:.1f}" width="{2*r}" height="{1.6 - i*0.15:.2f}" fill="{BG}"/>'
        )
    return "".join(tris) + "".join(cuts)


def lowpoly_band(width: float, base_y: float, amp: float, *, seed: int,
                 segments: int = 24, lo: str = INDIGO, hi: str = CYAN,
                 freq: float = 3.0, heights: Iterable[float] | None = None) -> str:
    """Triangulated mountain band with flat-shaded facets.

    The silhouette is driven either by procedural :func:`value_noise` or by an
    explicit ``heights`` sequence (values in ``[0, 1]``) — the latter lets real
    data (e.g. weekly contributions) sculpt the terrain. Each quad between two
    ridge samples is split into two triangles, each filled with one flat colour
    from the :data:`HEIGHT_RAMP` for the classic low-poly look.
    """
    noise = value_noise(seed)
    hs = list(heights) if heights is not None else None
    n = (len(hs) - 1) if hs else segments

    def ridge(i: int) -> float:
        h = hs[i] if hs else noise(i / n * freq)
        return base_y - amp * h

    facets = []
    for i in range(n):
        x0, x1 = width * i / n, width * (i + 1) / n
        y0, y1 = ridge(i), ridge(i + 1)
        for (ax, ay), (bx, by), (ccx, ccy) in (
            ((x0, y0), (x1, y1), (x0, base_y)),
            ((x1, y1), (x1, base_y), (x0, base_y)),
        ):
            depth = 1 - (((ay + by + ccy) / 3 - (base_y - amp)) / amp)
            color = lerp(lo, hi, max(0.0, min(1.0, depth)))
            facets.append(
                f'<polygon points="{ax:.1f},{ay:.1f} {bx:.1f},{by:.1f} {ccx:.1f},{ccy:.1f}" '
                f'fill="{color}" stroke="{color}" stroke-width="0.5"/>'
            )
    return "".join(facets)


def starfield(width: float, count: int = 7, *, max_y: float = 90,
              seed: int = 7) -> str:
    """Scattered twinkling stars across the top of a scene."""
    noise = value_noise(seed)
    stars = []
    for i in range(count):
        x = noise(i * 1.7) * width
        y = noise(i * 3.1 + 0.5) * max_y
        dur = 2.4 + noise(i * 5.3) * 1.6
        stars.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="1.2" fill="#ffffff">'
            f'<animate attributeName="opacity" values="0.2;1;0.2" dur="{dur:.1f}s" '
            f'repeatCount="indefinite"/></circle>'
        )
    return "".join(stars)
