"""GitHub data layer: fetch profile stats via GraphQL and aggregate them.

Separated from rendering so the network/format concerns live in one place and
the card renderers receive a single, flat :class:`Profile` dataclass (KISS).
Pure standard library — no third-party HTTP client.
"""
from __future__ import annotations

import json
import os
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass, field

API = "https://api.github.com/graphql"
PLACEHOLDER_COLOR = "#bf00ff"  # neon purple used for first-run blank language row

_QUERY = """
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


@dataclass
class Profile:
    """Flat snapshot of a user's public/visible GitHub activity."""

    name: str
    login: str
    followers: int
    stars: int
    commits: int
    prs: int
    issues: int
    repos: int
    total_contrib: int
    #: ``[(language, fraction, color), ...]`` sorted by size, top 8.
    langs: list[tuple[str, float, str]] = field(default_factory=list)
    #: Per-week contribution totals (chronological), used to sculpt terrain.
    weekly: list[int] = field(default_factory=list)

    @property
    def level(self) -> int:
        """Playful RPG level derived from lifetime-ish contribution volume."""
        return max(1, int((self.total_contrib / 100) ** 0.5) + 1)

    @property
    def xp_fraction(self) -> float:
        """Progress (``0..1``) from the current :attr:`level` to the next."""
        base = (self.level - 1) ** 2 * 100
        nxt = self.level**2 * 100
        span = nxt - base or 1
        return max(0.0, min(1.0, (self.total_contrib - base) / span))


def _request(login: str, token: str) -> dict:
    """POST the GraphQL query and return the decoded ``user`` object."""
    body = json.dumps({"query": _QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-profile-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError("GraphQL errors: " + json.dumps(payload["errors"]))
    return payload["data"]["user"]


def _aggregate(user: dict) -> Profile:
    """Reduce the raw GraphQL ``user`` object into a :class:`Profile`."""
    contrib = user["contributionsCollection"]
    calendar = contrib["contributionCalendar"]
    repos = user["repositories"]["nodes"]

    languages: "OrderedDict[str, dict]" = OrderedDict()
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            node = edge["node"]
            slot = languages.setdefault(node["name"], {"size": 0, "color": node["color"] or "#888"})
            slot["size"] += edge["size"]
    top = sorted(languages.items(), key=lambda kv: kv[1]["size"], reverse=True)[:8]
    total_size = sum(v["size"] for _, v in top) or 1

    weekly = [
        sum(day["contributionCount"] for day in week["contributionDays"])
        for week in calendar["weeks"]
    ]

    return Profile(
        name=user["name"] or user["login"],
        login=user["login"],
        followers=user["followers"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in repos),
        commits=contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"],
        prs=contrib["totalPullRequestContributions"],
        issues=contrib["totalIssueContributions"],
        repos=user["repositories"]["totalCount"],
        total_contrib=calendar["totalContributions"],
        langs=[(name, v["size"] / total_size, v["color"]) for name, v in top],
        weekly=weekly,
    )


def load(login: str | None = None, token: str | None = None) -> Profile:
    """Fetch and aggregate a :class:`Profile` from the GitHub API.

    ``login``/``token`` fall back to the ``GH_LOGIN`` and ``GH_TOKEN`` /
    ``GITHUB_TOKEN`` environment variables (as provided by GitHub Actions).
    """
    login = login or os.environ.get("GH_LOGIN", "rathosops")
    token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("ERROR: set GH_TOKEN (or GITHUB_TOKEN) in the environment.")
    return _aggregate(_request(login, token))


def placeholder(login: str = "rathosops") -> Profile:
    """A zeroed :class:`Profile` for first-run/offline rendering (honest blanks)."""
    return Profile(
        name=login, login=login, followers=0, stars=0, commits=0, prs=0, issues=0,
        repos=0, total_contrib=0,
        langs=[("run the workflow to populate", 1.0, PLACEHOLDER_COLOR)],
        weekly=[0] * 53,
    )
