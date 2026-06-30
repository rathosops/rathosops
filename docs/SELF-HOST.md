# Profile assets — 100% self-hosted, generated in this repo

The profile cards no longer depend on any third-party render service
(Vercel / Demolab). They are generated **by our own code** inside GitHub Actions
and committed back to the repo as static SVGs, so the README just serves files
from this repository. **No render-time dependency ⇒ no HTTP 429 ⇒ they never
silently disappear** in Chrome, Edge or Brave.

## How it works

```
scripts/gen_profile.py            our generator — pure Python stdlib, no pip deps
        │  queries GitHub GraphQL API with your token
        ▼
assets/stats.svg                  stat card (commits, PRs, issues, stars, ...)
assets/languages.svg              top languages bar + legend
assets/contributions.svg          last-year contribution calendar (animated)
        │  committed to the repo by
        ▼
.github/workflows/profile.yml     runs daily (and on demand), commits the SVGs
                                  + regenerates the contribution snake
```

Palette matches `assets/header.svg` (`#bf00ff / #ff2e97 / #00ffff / #1a0b2e`).

## One-time setup

### 1. (Recommended) Add a token so private stats count
The workflow falls back to the default `GITHUB_TOKEN` (public data only). To
include **private commits / contributions**, add a PAT:

1. GitHub → Settings → Developer settings → Personal access tokens →
   **Tokens (classic)** → Generate → scopes `repo` + `read:user` → copy it.
2. In this repo: Settings → Secrets and variables → Actions → **New repository
   secret** → name `PROFILE_TOKEN`, value = the token.

Without this secret everything still works — it just shows public numbers only.

### 2. Run it the first time
The committed `assets/*.svg` start as placeholder data. To populate real stats:

- GitHub → **Actions** tab → *Generate profile assets* → **Run workflow**.

After it finishes it commits the real SVGs and the README updates automatically.
From then on it refreshes **daily** (cron `17 4 * * *`).

### 3. Snake animation
The same workflow generates the contribution snake into the `output` branch
(referenced by the `$ ./snake.sh --render` section). First run may take a minute;
until then the snake image 404s — that's expected.

## Run / preview locally (optional)

```bash
export GH_TOKEN=<your_pat>      # or a fine-grained token with read:user
export GH_LOGIN=rathosops
python scripts/gen_profile.py   # writes assets/stats|languages|contributions.svg
```

No dependencies to install — standard library only.

## Customizing

- **Colors / theme:** edit the palette constants at the top of
  `scripts/gen_profile.py` (`BG`, `PINK`, `CYAN`, ...).
- **Which stats / layout:** edit `render_stats`, `render_languages`,
  `render_contributions` in the same file.
- **Refresh frequency:** change the `cron` in `.github/workflows/profile.yml`.

Everything is our own code — nothing to deploy, no external account, no rate limit.
