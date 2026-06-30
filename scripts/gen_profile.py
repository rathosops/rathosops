#!/usr/bin/env python3
"""
Self-hosted GitHub profile asset generator — no third-party render services.

Queries the GitHub GraphQL API with a token (provided by GitHub Actions or the
local environment) and renders vaporwave-themed SVGs committed to this repo:

    assets/stats.svg          career/activity stat card
    assets/languages.svg      top languages bar + legend
    assets/contributions.svg  last-year contribution calendar (animated)

Pure standard library — no pip dependencies. Palette matches assets/header.svg.

Env:
    GH_TOKEN   GitHub token (PAT classic with `repo,read:user` for private stats,
               or the default Actions GITHUB_TOKEN for public-only).
    GH_LOGIN   target username (default: rathosops)
"""
import json
import os
import sys
import urllib.request
from collections import OrderedDict

LOGIN = os.environ.get("GH_LOGIN", "rathosops")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

# ── vaporwave palette (matches assets/header.svg) ────────────────────────────
BG = "#1a0b2e"
BG2 = "#241046"
PINK = "#ff2e97"
PINK2 = "#ff6bd6"
PURPLE = "#bf00ff"
CYAN = "#00ffff"
TEXT = "#e0c3fc"
INDIGO = "#3a0ca3"

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
      totalRepositoryContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def fetch():
    if not TOKEN:
        sys.exit("ERROR: set GH_TOKEN (or GITHUB_TOKEN) in the environment.")
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": f"{LOGIN}-profile-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        sys.exit("GraphQL errors: " + json.dumps(payload["errors"], indent=2))
    return payload["data"]["user"]


def aggregate(user):
    cc = user["contributionsCollection"]
    repos = user["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)

    langs = OrderedDict()
    for r in repos:
        for edge in r["languages"]["edges"]:
            n = edge["node"]["name"]
            if n not in langs:
                langs[n] = {"size": 0, "color": edge["node"]["color"] or "#888"}
            langs[n]["size"] += edge["size"]
    top = sorted(langs.items(), key=lambda kv: kv[1]["size"], reverse=True)[:8]
    total_size = sum(v["size"] for _, v in top) or 1

    days = []
    for week in cc["contributionCalendar"]["weeks"]:
        for d in week["contributionDays"]:
            days.append(d["contributionCount"])

    return {
        "name": user["name"] or user["login"],
        "login": user["login"],
        "followers": user["followers"]["totalCount"],
        "stars": stars,
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"],
        "repos": user["repositories"]["totalCount"],
        "total_contrib": cc["contributionCalendar"]["totalContributions"],
        "langs": [(n, v["size"] / total_size, v["color"]) for n, v in top],
        "weeks": cc["contributionCalendar"]["weeks"],
    }


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ── shared SVG fragments ─────────────────────────────────────────────────────
def defs():
    return f"""
  <defs>
    <linearGradient id="title" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{PINK2}"/>
      <stop offset="100%" stop-color="{CYAN}"/>
    </linearGradient>
    <linearGradient id="frame" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PINK2}"/>
      <stop offset="50%" stop-color="{PURPLE}"/>
      <stop offset="100%" stop-color="{CYAN}"/>
    </linearGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{BG2}"/>
      <stop offset="100%" stop-color="{BG}"/>
    </linearGradient>
  </defs>"""


def frame(w, h, title):
    return f"""
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="10" fill="url(#panel)"
        stroke="url(#frame)" stroke-width="1.5"/>
  <rect x="0" y="0" width="{w}" height="2.5" fill="{CYAN}" opacity="0.08">
    <animate attributeName="y" values="-3;{h}" dur="5s" repeatCount="indefinite"/>
  </rect>
  <text x="18" y="30" font-family="'Press Start 2P', monospace" font-size="13"
        fill="url(#title)">&#9656; {esc(title)}</text>
  <line x1="18" y1="40" x2="{w-18}" y2="40" stroke="{PURPLE}" stroke-width="1" opacity="0.4"/>"""


# ── stats card ───────────────────────────────────────────────────────────────
def render_stats(d):
    w, h = 460, 200
    rows = [
        ("commits", "commits (this year)", d["commits"]),
        ("merge", "pull requests", d["prs"]),
        ("bug", "issues", d["issues"]),
        ("star", "stars earned", d["stars"]),
        ("repo", "public repositories", d["repos"]),
        ("users", "followers", d["followers"]),
    ]
    y = 64
    body = []
    for i, (_, label, value) in enumerate(rows):
        ry = y + i * 21
        body.append(
            f'<text x="22" y="{ry}" font-family="monospace" font-size="13" fill="{TEXT}">'
            f'<tspan fill="{PINK}">&#9656;</tspan> {esc(label)}</text>'
            f'<text x="{w-22}" y="{ry}" text-anchor="end" font-family="monospace" '
            f'font-size="13" font-weight="700" fill="{CYAN}">{value:,}</text>'
        )
    total = (
        f'<text x="{w/2}" y="192" text-anchor="middle" font-family="monospace" '
        f'font-size="11" fill="{PINK2}">{d["total_contrib"]:,} contributions in the last year</text>'
    )
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub stats">'
        + defs() + frame(w, h, f"{esc(d['login'])} :: stats")
        + "".join(body) + total + "</svg>\n"
    )


# ── languages card ───────────────────────────────────────────────────────────
def render_languages(d):
    w, h = 460, 200
    bar_y, bar_x, bar_w, bar_h = 58, 18, w - 36, 16
    segs, x = [], bar_x
    for name, frac, color in d["langs"]:
        seg = max(frac * bar_w, 0)
        segs.append(
            f'<rect x="{x:.1f}" y="{bar_y}" width="{seg:.1f}" height="{bar_h}" fill="{color}">'
            f'<title>{esc(name)} {frac*100:.1f}%</title></rect>'
        )
        x += seg
    # rounded mask via overlay border
    segs.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="4" '
        f'fill="none" stroke="{PURPLE}" stroke-width="1" opacity="0.6"/>'
    )
    # legend grid 2 cols x 4
    legend, ly = [], 96
    for i, (name, frac, color) in enumerate(d["langs"]):
        col = i % 2
        row = i // 2
        lx = bar_x + col * (bar_w / 2)
        yy = ly + row * 24
        legend.append(
            f'<circle cx="{lx+6}" cy="{yy-4}" r="5" fill="{color}"/>'
            f'<text x="{lx+18}" y="{yy}" font-family="monospace" font-size="12" fill="{TEXT}">'
            f'{esc(name)} <tspan fill="{CYAN}">{frac*100:.1f}%</tspan></text>'
        )
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Top languages">'
        + defs() + frame(w, h, f"{esc(d['login'])} :: languages")
        + "".join(segs) + "".join(legend) + "</svg>\n"
    )


# ── contribution calendar (animated) ─────────────────────────────────────────
def contrib_color(count, mx):
    if count <= 0:
        return "#2a1a44"
    t = count / mx if mx else 0
    stops = [(0.0, INDIGO), (0.4, PURPLE), (0.7, PINK), (1.0, CYAN)]
    for i in range(len(stops) - 1):
        a, ca = stops[i]
        b, cb = stops[i + 1]
        if t <= b:
            f = (t - a) / (b - a) if b > a else 0
            return lerp(ca, cb, f)
    return CYAN


def lerp(c1, c2, f):
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r = round(int(c1[0:2], 16) + (int(c2[0:2], 16) - int(c1[0:2], 16)) * f)
    g = round(int(c1[2:4], 16) + (int(c2[2:4], 16) - int(c1[2:4], 16)) * f)
    b = round(int(c1[4:6], 16) + (int(c2[4:6], 16) - int(c1[4:6], 16)) * f)
    return f"#{r:02x}{g:02x}{b:02x}"


def render_contributions(d):
    weeks = d["weeks"]
    cell, gap = 11, 3
    ncols = len(weeks)
    grid_w = ncols * (cell + gap)
    pad_x, pad_y = 18, 52
    w = grid_w + pad_x * 2
    h = pad_y + 7 * (cell + gap) + 28
    mx = max((day["contributionCount"] for week in weeks for day in week["contributionDays"]), default=1)

    cells = []
    for ci, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            cx = pad_x + ci * (cell + gap)
            cy = pad_y + di * (cell + gap)
            color = contrib_color(day["contributionCount"], mx)
            cells.append(
                f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" rx="2" fill="{color}">'
                f'<title>{esc(day["date"])}: {day["contributionCount"]}</title></rect>'
            )
    # animated neon sweep column
    sweep = (
        f'<rect x="{pad_x}" y="{pad_y}" width="{cell}" height="{7*(cell+gap)-gap}" '
        f'rx="2" fill="{CYAN}" opacity="0.18">'
        f'<animate attributeName="x" values="{pad_x};{pad_x+grid_w-cell}" '
        f'dur="3.5s" repeatCount="indefinite"/></rect>'
    )
    total = (
        f'<text x="{w-pad_x}" y="{h-12}" text-anchor="end" font-family="monospace" '
        f'font-size="11" fill="{PINK2}">{d["total_contrib"]:,} contributions in the last year</text>'
    )
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Contribution activity">'
        + defs() + frame(w, h, "contribution activity")
        + "".join(cells) + sweep + total + "</svg>\n"
    )


def main():
    user = fetch()
    d = aggregate(user)
    out = {
        "assets/stats.svg": render_stats(d),
        "assets/languages.svg": render_languages(d),
        "assets/contributions.svg": render_contributions(d),
    }
    for path, svg in out.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
