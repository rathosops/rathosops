"""Render the static terminal blocks as styled vaporwave SVG windows.

Each former Markdown code block (neofetch, /proc/self/status, ~/.pipeline.yml,
htop, tree, journalctl) becomes a :func:`svgkit.window` with consistent chrome,
syntax-ish colouring and a low-poly decorative icon, so the whole README shares
one aesthetic. Content is static, so these renderers ignore live profile data.
"""
from __future__ import annotations

import svgkit as k

COMMENT = "#9d7bd8"   # muted purple for comments / chrome
KEY = k.CYAN          # identifiers / keys
ACCENT = k.PINK       # labels / tags
VALUE = k.TEXT        # plain values
OK = "#7CFFB0"        # done / running


def _comment(line: str) -> list:
    """Colour a whole-line comment in muted purple."""
    return [(line, COMMENT)]


def _kv(key: str, value: str, *, pad: int = 12) -> list:
    """A ``key ▸ value`` row with an accent key and plain value."""
    return [(f"{key.ljust(pad)}", ACCENT), ("▸  ", k.PURPLE), (value, VALUE)]


# ── $ neofetch ────────────────────────────────────────────────────────────────
_ARCH_LOGO = [
    "      -`", "     .o+`", "    `ooo/", "   `+oooo:", "  `+oooooo:",
    "  -+oooooo+:", "`/:-:++oooo+:", "`/++++/+++++++:", "`/++++++++++++++:",
    "`/+++ooooooooooooo/`", "./ooosssso++osssssso+`", ".oossssso-````/ossssss+`",
    "-osssssso.      :ssssssso.", ":osssssss/        osssso+++.",
    "/ossssssss/        +ssssooo/-", "`/ossssso+/:-        -:/+osssso+-",
    "`+sso+:-`                 `.-/+oso:", "`++:.                           `-/+/",
    ".`                                 `/",
]
_NEOFETCH_INFO = [
    ("OS", "Arch Linux (btw)"), ("Kernel", "6.x.x-arch-hardened"),
    ("Shell", "zsh + tmux"), ("WM", "Hyprland"), ("Editor", "Neovim (obviously)"),
    ("Theme", "Synthwave '84"), ("Path", "Backend ──► DevOps"),
    ("Focus", "CI/CD + Security + Cloud"), ("Cloud", "AWS"),
    ("Uptime", "coding since 2019"), ("Packages", "docker git python go terraform"),
    ("Terminal", "kitty / alacritty"), ("Mission", "automate everything, secure it all"),
]


def render_neofetch() -> str:
    """Arch ASCII logo beside the system-info column, CRT icon in the corner."""
    width, rows = 760, len(_ARCH_LOGO) + 1
    logo = k.mono_rows([[(ln, KEY)] for ln in _ARCH_LOGO], x=22, size=12)
    info = k.mono_rows(
        [[("rathosops", k.PINK2), ("@", COMMENT), ("github", KEY)],
         [("─" * 30, COMMENT)],
         *[_kv(key, val) for key, val in _NEOFETCH_INFO]],
        x=250, size=12,
    )
    return k.window(width, "$ neofetch", logo + info, rows=rows,
                    decoration=k.icon_crt(width - 56, 52, 0.95))


# ── $ cat /proc/self/status ──────────────────────────────────────────────────
def render_status() -> str:
    """Career snapshot as a coloured YAML-ish window."""
    rows = [
        _comment("# rathosops career snapshot"),
        "",
        [("Name", ACCENT), ("       Athos Aurélio", VALUE)],
        [("Handle", ACCENT), ("     rathosops", VALUE)],
        [("Role", ACCENT), ("       Senior Backend Engineer → DevOps / DevSecOps", VALUE)],
        [("Location", ACCENT), ("   Brazil (São Paulo state)", VALUE)],
        [("Mission", ACCENT), ('    "secure, automated and observable delivery pipelines"', k.PINK2)],
        "",
        _comment("# ── trajectory ───────────────────────────────────────"),
        [("current_role", KEY), (": Senior Backend Engineer @ real production", VALUE)],
        [("target_path", KEY), (": DevOps / DevSecOps / Platform Eng / SRE", VALUE)],
        [("open_to", KEY), (": [ Junior DevOps, Cloud Eng, SRE, DevSecOps ]", VALUE)],
        "",
        _comment("# ── stack ────────────────────────────────────────────"),
        [("base", KEY), ("   : Python, Go, FastAPI, Flask, Django, Docker, AWS", VALUE)],
        [("target", KEY), (" : Kubernetes, Terraform, GH Actions, LGTM, IaC", VALUE)],
        "",
        _comment("# ── principles ───────────────────────────────────────"),
        [('  "If you ran it manually, you haven\'t shipped it."', k.PINK2)],
        [('  "Security is not a phase. It\'s a pipeline stage."', k.PINK2)],
        [('  "Observability is the difference between ops and guessing."', k.PINK2)],
    ]
    return k.window(720, "$ cat /proc/self/status", k.mono_rows(rows), rows=len(rows),
                    decoration=k.icon_pizza(720 - 50, 50, 0.7))


# ── $ cat ~/.pipeline.yml ────────────────────────────────────────────────────
def _stage(name: str, items: list[tuple[str, str]]) -> list:
    """Build rows for one pipeline stage (header + commented list items)."""
    rows: list = [[(f"  {name}", KEY), (":", VALUE)]]
    for tool, note in items:
        rows.append([(f"    - {tool.ljust(14)}", VALUE), (f"# {note}", COMMENT)])
    return rows


def render_pipeline() -> str:
    """The secure-delivery pipeline as a coloured YAML window with a gamepad."""
    rows = [_comment("# ~/.pipeline.yml — secure delivery standard"), "",
            [("pipeline", KEY), (":", VALUE)]]
    rows += _stage("code_quality", [("ruff", "python lint"), ("pytest", "unit tests"),
                                    ("coverage", "80% gate")])
    rows += _stage("security", [("semgrep", "SAST"), ("bandit", "py security"),
                                ("gitleaks", "secrets"), ("trivy", "container scan"),
                                ("osv-scanner", "dep CVEs")])
    rows += _stage("supply_chain", [("sbom", "syft"), ("cosign", "image signing"),
                                    ("dependabot", "dep updates")])
    rows += _stage("delivery", [("docker", "minimal image"), ("github_actions", "CI/CD"),
                                ("aws_ecr", "registry"), ("kubernetes", "deploy target")])
    rows += _stage("observability", [("prometheus", "metrics"), ("grafana", "dashboards"),
                                     ("loki", "logs"), ("tempo", "traces"),
                                     ("otel", "telemetry")])
    rows += [[("  policy", KEY), (":", VALUE)],
             [("    fail_on_critical", VALUE), (": ", VALUE), ("true", OK)],
             [("    block_unsigned_images", VALUE), (": ", VALUE), ("true", OK)],
             [("    require_sbom", VALUE), (": ", VALUE), ("true", OK)]]
    return k.window(720, "$ cat ~/.pipeline.yml", k.mono_rows(rows), rows=len(rows),
                    decoration=k.icon_gamepad(720 - 60, 52, 0.8))


# ── $ htop ───────────────────────────────────────────────────────────────────
_PROCS = [
    ("001", "pgfn/dide2", 1.0, "automação de dados governamentais"),
    ("002", "rathosops/observability", 1.0, "LGTM stack + OpenTelemetry labs"),
    ("003", "locacamba", 0.75, "sistema de gestão para cliente final"),
    ("004", "aws-devops-lab", 0.5, "hands-on EC2 + ECR + CloudWatch"),
    ("005", "terraform-aws-lab", 0.5, "provisionando infra como código"),
    ("006", "k8s-platform-lab", 0.25, "helm charts + ingress + HPA"),
    ("007", "cert/aws-ccp", 0.25, "cloud practitioner prep"),
]


def render_htop() -> str:
    """Active projects as an htop-style window with coloured load bars."""
    rows: list = [[("PID  PROCESS".ljust(30), COMMENT), ("LOAD          TASK", COMMENT)],
                  [("─" * 64, COMMENT)]]
    for pid, name, load, task in _PROCS:
        bar = "█" * round(load * 8)
        rows.append([
            (pid + "  ", k.PINK2),
            (f"[{name}]".ljust(28), KEY),
            (bar.ljust(9), k.ramp(load)),
            (task, VALUE),
        ])
    rows += [[("─" * 64, COMMENT)],
             [("Load: ", COMMENT), ("high", ACCENT), ("   Uptime: ", COMMENT),
              ("always", KEY), ("   Coffee: ", COMMENT), ("ongoing", k.PINK2)]]
    return k.window(760, "$ htop — what's running now", k.mono_rows(rows), rows=len(rows),
                    decoration=k.icon_crt(760 - 56, 52, 0.9))


# ── $ tree ~/devops-labs ─────────────────────────────────────────────────────
_TREE = [
    ("observability-lab", "FastAPI + LGTM + OpenTelemetry + GH Actions", False),
    ("dockerized-python-api", "Multi-stage Dockerfile + Trivy + Compose", False),
    ("nginx-reverse-proxy-lab", "TLS + rate limiting + hardened headers", False),
    ("ci-cd-secure-api", "SAST + SCA + secrets + container scan", False),
    ("aws-devops-lab", "EC2 + ECR + S3 + CloudWatch", True),
    ("k8s-platform-lab", "Deployments + Ingress + Helm + HPA", True),
    ("devsecops-pipeline-templ", "Semgrep + Gitleaks + Trivy + SBOM + Cosign", False),
    ("terraform-aws-lab", "IaC: entire AWS infra as code", True),
    ("GateHunter", "Port scanner / service mapper (Python)", False),
    ("my_dots", "Arch + Hyprland + Neovim + tmux dotfiles", False),
]


def render_tree() -> str:
    """Repo tree with branch glyphs, cyan names and 'in progress' tags."""
    rows: list = [[("~/devops-labs", k.PINK2)]]
    for i, (name, desc, wip) in enumerate(_TREE):
        glyph = "└── " if i == len(_TREE) - 1 else "├── "
        row = [(glyph, k.PURPLE), (name.ljust(26), KEY), ("← ", COMMENT), (desc, VALUE)]
        if wip:
            row.append(("  [wip]", ACCENT))
        rows.append(row)
    return k.window(760, "$ tree ~/devops-labs --annotated", k.mono_rows(rows),
                    rows=len(rows), decoration=k.icon_pizza(760 - 50, 50, 0.7))


# ── $ journalctl ─────────────────────────────────────────────────────────────
_MISSION = [
    ("May 2026", "INFO", "linux + networking + docker fundamentals", "RUNNING"),
    ("Jun 2026", "INFO", "github actions + ci/cd + devsecops pipelines", "QUEUED"),
    ("Jun 2026", "CERT", "AWS Cloud Practitioner", "QUEUED"),
    ("Jul 2026", "INFO", "aws hands-on: ec2 + ecr + s3 + cloudwatch", "QUEUED"),
    ("Aug 2026", "INFO", "terraform: infra as code para tudo acima", "QUEUED"),
    ("Aug 2026", "INFO", "kubernetes: helm + hpa + ingress", "QUEUED"),
    ("Sep 2026", "CERT", "HashiCorp Terraform Associate", "QUEUED"),
    ("Sep 2026", "INFO", "devsecops: sast + sca + sbom + cosign", "QUEUED"),
    ("Oct 2026", "INFO", "observability: runbooks + alerting + slos", "QUEUED"),
    ("Nov 2026", "INFO", "iac + gitops: argocd + opentofu", "QUEUED"),
    ("Dec 2026", "APPLY", "portfolio final + devops junior applications", "QUEUED"),
]
_TAG_COLOR = {"INFO": k.CYAN, "CERT": k.PINK, "APPLY": k.PINK2}


def render_journalctl() -> str:
    """Mission roadmap log with coloured level tags and status."""
    rows = []
    for when, tag, msg, status in _MISSION:
        rows.append([
            (when + "  ", COMMENT),
            (f"[{tag}]".ljust(8), _TAG_COLOR[tag]),
            (msg.ljust(46), VALUE),
            (f"[{status}]", OK if status == "RUNNING" else k.PURPLE),
        ])
    return k.window(760, "$ journalctl -f /var/log/mission-2026.log",
                    k.mono_rows(rows), rows=len(rows),
                    decoration=k.icon_gamepad(760 - 60, 52, 0.8))


#: filename -> renderer, consumed by gen_profile.
TERMINALS = {
    "term_neofetch.svg": render_neofetch,
    "term_status.svg": render_status,
    "term_pipeline.svg": render_pipeline,
    "term_htop.svg": render_htop,
    "term_tree.svg": render_tree,
    "term_journalctl.svg": render_journalctl,
}
