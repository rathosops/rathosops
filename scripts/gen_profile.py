#!/usr/bin/env python3
"""Generate the retro / low-poly profile SVGs and write them to ``assets/``.

Thin orchestrator: pull a :class:`~github_data.Profile`, compose the cards from
:mod:`svgkit` primitives, and persist them. Run in CI by
``.github/workflows/profile.yml`` (and locally with ``GH_TOKEN`` set).

Generated assets
----------------
``header.svg``        low-poly retrowave scene + title
``stats.svg``         RPG character sheet (LEVEL, XP, attribute bars)
``languages.svg``     "equipped skills" loadout with pixel proficiency bars
``contributions.svg`` contribution heightmap as low-poly 3D terrain
``typing.svg``        animated RPG dialogue box
``footer.svg``        low-poly mountain silhouette + tagline
"""
from __future__ import annotations

import os

import svgkit as k
from github_data import Profile, load, placeholder
from terminals import TERMINALS

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")

TAGLINE_LINES = [
    "Backend Engineer -> DevOps / DevSecOps",
    "If it's not in a pipeline, it doesn't ship.",
    "Shift-left or go home.",
    "btw I use Arch.",
    "Linux is not an OS. It's a religion.",
    "I don't deploy manually. I'm not an animal.",
]


# ── header ────────────────────────────────────────────────────────────────────
def render_header(p: Profile) -> str:
    """Low-poly retrowave hero: faceted sun, layered mountains, neon title."""
    w, h = 1200, 300
    sky = k.linear_gradient("sky", [(0, k.BG), (0.5, k.INDIGO), (1, "#7209b7")], x2=0, y2=1)
    scene = (
        f"<defs>{sky}</defs>"
        f'<rect width="{w}" height="{h}" fill="url(#sky)"/>'
        + k.starfield(w, count=9, max_y=110)
        + k.faceted_sun(w / 2, 175, 72)
        + k.lowpoly_band(w, 250, 70, seed=11, segments=20, lo=k.INDIGO, hi=k.PURPLE)
        + k.lowpoly_band(w, 300, 110, seed=4, segments=16, lo="#2a0f4a", hi=k.PINK)
        + k.scanline(w, h)
        + k.text(w / 2, 90, "rathosops", size=44, fill="#ffffff", font=k.PIXEL,
                 anchor="middle", weight=700)
        + k.text(w / 2, 122, "&#9656; backend &#8594; secure, automated &amp; observable pipelines &#9666;",
                 size=13, fill=k.CYAN, anchor="middle", spacing=1)
        + f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="none" '
        f'stroke="{k.PINK2}" stroke-width="1.5" opacity="0.7"/>'
    )
    return k.document(w, h, scene, label="rathosops — low-poly retrowave header")


# ── stats: RPG character sheet ────────────────────────────────────────────────
def render_stats(p: Profile) -> str:
    """Stats as an RPG sheet: LEVEL badge, XP bar and four attribute bars."""
    w, h = 460, 210
    attrs = [("ATK", p.commits, "commits"), ("DEF", p.prs, "pull reqs"),
             ("MAG", p.issues, "issues"), ("LCK", p.stars, "stars")]
    cap = max((v for _, v, _ in attrs), default=1) or 1

    body = [
        k.panel(w, h, f"player :: {k.esc(p.login)}"),
        k.text(w - 18, 30, f"LV {p.level}", size=13, fill=k.CYAN, font=k.PIXEL, anchor="end"),
        k.text(22, 60, "XP", size=11, fill=k.PINK2, font=k.PIXEL),
        k.pixel_bar(60, 50, w - 80, 12, p.xp_fraction, segments=24, color=k.CYAN),
        k.text(w - 18, 60, f"{p.total_contrib:,}", size=11, fill=k.TEXT, anchor="end"),
    ]
    y = 92
    for i, (label, value, sub) in enumerate(attrs):
        ry = y + i * 27
        body += [
            k.text(22, ry, label, size=11, fill=k.PINK, font=k.PIXEL),
            k.pixel_bar(72, ry - 11, 250, 12, value / cap, segments=20,
                        color=k.ramp(value / cap)),
            k.text(w - 18, ry, f"{value:,} {sub}", size=12, fill=k.TEXT, anchor="end"),
        ]
    body.append(
        k.text(w / 2, 202, f"REPOS {p.repos:,}  &#9670;  FOLLOWERS {p.followers:,}",
               size=11, fill=k.PINK2, anchor="middle")
    )
    return k.document(w, h, *body, label="GitHub stats — RPG character sheet")


# ── languages: equipped skills ───────────────────────────────────────────────
def render_languages(p: Profile) -> str:
    """Top languages as an "equipped skills" loadout with proficiency bars."""
    w, h = 460, 210
    body = [k.panel(w, h, f"{k.esc(p.login)} :: equipped skills")]
    rows = p.langs[:6]
    y = 70
    for i, (name, frac, color) in enumerate(rows):
        ry = y + i * 23
        body += [
            f'<circle cx="26" cy="{ry-4}" r="5" fill="{color}"/>',
            k.text(40, ry, k.esc(name), size=12, fill=k.TEXT),
            k.pixel_bar(190, ry - 11, 180, 11, frac, segments=18, color=color),
            k.text(w - 18, ry, f"{frac*100:.1f}%", size=12, fill=k.CYAN, anchor="end"),
        ]
    return k.document(w, h, *body, label="Top languages — equipped skills")


# ── contributions: low-poly 3D terrain ───────────────────────────────────────
def render_contributions(p: Profile) -> str:
    """Weekly contributions sculpted into a flat-shaded low-poly terrain."""
    w, h = 720, 240
    base_y, amp = 212, 138
    mx = max(p.weekly, default=1) or 1
    heights = [v / mx for v in p.weekly]

    sweep = (
        f'<rect x="18" y="52" width="3" height="{base_y-52}" fill="{k.CYAN}" opacity="0.25">'
        f'<animate attributeName="x" values="18;{w-21}" dur="4s" repeatCount="indefinite"/></rect>'
    )
    body = [
        k.panel(w, h, "contribution terrain"),
        k.lowpoly_band(w, base_y, 60, seed=21, segments=28, lo="#221042", hi=k.INDIGO),
        k.lowpoly_band(w, base_y, amp, seed=3, segments=len(heights) - 1,
                       lo=k.INDIGO, hi=k.CYAN, heights=heights),
        sweep,
        k.text(w - 18, h - 14, f"{p.total_contrib:,} contributions in the last year",
               size=11, fill=k.PINK2, anchor="end"),
    ]
    return k.document(w, h, *body, label="Contribution activity — low-poly terrain")


# ── typing: RPG dialogue box ─────────────────────────────────────────────────
def _cycling_text(x: float, y: float, lines: list[str], *, slot: float = 2.9) -> str:
    """Opacity-cycled text lines sharing one timeline (perfectly synced)."""
    cycle = len(lines) * slot
    out = []
    for i, line in enumerate(lines):
        a, b = i / len(lines), (i + 1) / len(lines)
        f = 0.012
        keytimes = [0, max(a - f, 0), a + f, b - f, min(b + f, 1), 1]
        for j in range(1, len(keytimes)):
            keytimes[j] = max(keytimes[j], keytimes[j - 1] + 1e-4)
        kt = ";".join(f"{t:.4f}" for t in keytimes)
        out.append(
            f'<text x="{x}" y="{y}" font-family="{k.PIXEL}" font-size="13" '
            f'fill="url(#title)" opacity="0">{k.esc(line)}'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" '
            f'dur="{cycle}s" repeatCount="indefinite"/></text>'
        )
    return "".join(out)


def render_typing(p: Profile) -> str:
    """An 8-bit RPG dialogue box that types out the tagline lines."""
    w, h = 720, 96
    box = (
        k.SHARED_DEFS
        + f'<rect x="3" y="3" width="{w-6}" height="{h-6}" rx="6" fill="url(#panel)" '
        f'stroke="url(#frame)" stroke-width="2"/>'
        + f'<rect x="9" y="9" width="{w-18}" height="{h-18}" rx="4" fill="none" '
        f'stroke="{k.PURPLE}" stroke-width="1" opacity="0.5"/>'
        + k.text(22, h / 2 + 5, "&#9656;", size=14, fill=k.PINK, font=k.PIXEL)
        + _cycling_text(46, h / 2 + 5, TAGLINE_LINES)
        + f'<rect x="{w-26}" y="{h-22}" width="9" height="9" fill="{k.CYAN}">'
        f'<animate attributeName="opacity" values="1;0;1" dur="0.9s" repeatCount="indefinite"/></rect>'
    )
    return k.document(w, h, box, label="Backend Engineer dialogue box")


# ── footer ────────────────────────────────────────────────────────────────────
def render_footer(p: Profile) -> str:
    """Low-poly mountain silhouette with the mission tagline."""
    w, h = 1200, 140
    body = (
        f'<rect width="{w}" height="{h}" fill="{k.BG}"/>'
        + k.starfield(w, count=6, max_y=40)
        + k.lowpoly_band(w, h, 90, seed=9, segments=26, lo=k.INDIGO, hi=k.PINK)
        + k.text(w / 2, 40, "automate everything. secure it all.", size=18,
                 fill=k.CYAN, anchor="middle", weight=700, spacing=1)
    )
    return k.document(w, h, body, label="automate everything. secure it all.")


RENDERERS = {
    "header.svg": render_header,
    "stats.svg": render_stats,
    "languages.svg": render_languages,
    "contributions.svg": render_contributions,
    "typing.svg": render_typing,
    "footer.svg": render_footer,
}


def _write(out_dir: str, filename: str, svg: str) -> None:
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(svg)
    print(f"wrote {os.path.normpath(path)}")


def build(profile: Profile, out_dir: str = ASSETS) -> None:
    """Render every data card and static terminal window under ``out_dir``."""
    os.makedirs(out_dir, exist_ok=True)
    for filename, renderer in RENDERERS.items():
        _write(out_dir, filename, renderer(profile))
    for filename, renderer in TERMINALS.items():
        _write(out_dir, filename, renderer())


def main() -> None:
    """Load live data when a token is present, else render honest placeholders."""
    has_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    build(load() if has_token else placeholder())


if __name__ == "__main__":
    main()
