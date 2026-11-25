#!/usr/bin/env python3
"""Generate a dynamic, animated ASCII telemetry SVG for nicko-guest's GitHub profile."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import html
import json
import os
from pathlib import Path
import urllib.error
import urllib.request


USERNAME = os.environ.get("GITHUB_USERNAME", "nicko-guest")
MANILA_TZ = timezone(timedelta(hours=8))
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "telemetry-sync.svg"


def fetch_json(url: str, token: str | None = None) -> dict | list:
    """Fetch JSON from the GitHub REST API using stdlib urllib."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_telemetry(username: str, token: str | None) -> dict:
    """Collect live GitHub user and repository telemetry."""
    user = fetch_json(f"https://api.github.com/users/{username}", token)
    repos = fetch_json(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed",
        token,
    )

    own_repos = [r for r in repos if not r.get("fork")]
    total_stars = sum(int(r.get("stargazers_count", 0)) for r in own_repos)
    lang_counts = Counter(
        r["language"] for r in own_repos if r.get("language")
    )
    top_langs = [lang for lang, _ in lang_counts.most_common(4)]

    recent_repos = []
    for repo in own_repos[:3]:
        pushed = (repo.get("pushed_at") or "")[:10]
        recent_repos.append(
            {
                "name": repo.get("name", ""),
                "language": repo.get("language") or "Markdown",
                "stars": int(repo.get("stargazers_count", 0)),
                "pushed": pushed or "recent",
            }
        )

    now_ph = datetime.now(MANILA_TZ).strftime("%Y-%m-%d %H:%M UTC+8")

    return {
        "mode": "LIVE",
        "public_repos": str(user.get("public_repos", len(own_repos))),
        "followers": str(user.get("followers", 0)),
        "stars": str(total_stars),
        "top_langs": " · ".join(top_langs) if top_langs else "TypeScript · Python · PHP",
        "recent_repos": recent_repos,
        "synced_at": now_ph,
    }


def offline_telemetry() -> dict:
    """Return initial placeholder telemetry before the first GitHub Actions run."""
    return {
        "mode": "PENDING",
        "public_repos": "AUTO",
        "followers": "AUTO",
        "stars": "AUTO",
        "top_langs": "Synced automatically on GitHub Actions",
        "recent_repos": [
            {
                "name": "nicko-guest",
                "language": "Markdown / SVG",
                "stars": 0,
                "pushed": "auto-sync",
            }
        ],
        "synced_at": "Awaiting workflow run (UTC+8)",
    }


def truncate(text: str, limit: int) -> str:
    """Truncate text cleanly with ellipsis."""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def render_svg(data: dict) -> str:
    """Render an animated, responsive ASCII telemetry SVG."""
    esc = html.escape
    mode_label = "LIVE SYNC" if data["mode"] == "LIVE" else "AUTO-SYNC READY"
    dot_color = "#3ddc84" if data["mode"] == "LIVE" else "#F25912"

    recent_rows_svg = []
    y_pos = 186
    for idx, repo in enumerate(data["recent_repos"][:3], start=1):
        name = esc(truncate(repo["name"], 26))
        lang = esc(truncate(repo["language"], 16))
        pushed = esc(repo["pushed"])
        stars = f"★ {repo['stars']}"
        recent_rows_svg.append(
            f'  <text class="mono" x="488" y="{y_pos}" font-size="12" fill="#5B91A3" font-weight="700" xml:space="preserve">0{idx}</text>\n'
            f'  <text class="mono" x="516" y="{y_pos}" font-size="12" fill="#eeece8" font-weight="600" xml:space="preserve">{name}</text>\n'
            f'  <text class="mono" x="712" y="{y_pos}" font-size="11" fill="#eeece8" opacity="0.65" xml:space="preserve">{lang}</text>\n'
            f'  <text class="mono" x="814" y="{y_pos}" font-size="11" fill="#F25912" xml:space="preserve">{esc(stars)}</text>'
        )
        y_pos += 26

    if not recent_rows_svg:
        recent_rows_svg.append(
            '  <text class="mono" x="488" y="186" font-size="12" fill="#eeece8" opacity="0.7" xml:space="preserve">Waiting for public repository activity…</text>'
        )

    recent_block = "\n".join(recent_rows_svg)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 280" width="100%" role="img" aria-label="Dynamic GitHub Telemetry Panel">
  <defs>
    <style>
      .mono {{ font-family: ui-monospace, 'SFMono-Regular', Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }}
      @keyframes pulseBar {{
        0%, 100% {{ opacity: 0.95; }}
        50% {{ opacity: 0.45; }}
      }}
      .pulse {{ animation: pulseBar 2.4s ease-in-out infinite; }}
    </style>
  </defs>

  <rect x="8" y="8" width="884" height="264" rx="6" fill="#0a0a0a" stroke="#2a2a2a" stroke-width="1.5"/>

  <!-- Header -->
  <rect x="8" y="8" width="884" height="36" rx="6" fill="#141414"/>
  <rect x="8" y="38" width="884" height="6" fill="#141414"/>
  <line x1="8" y1="44" x2="892" y2="44" stroke="#262626" stroke-width="1"/>
  <text class="mono" x="26" y="31" font-size="12.5" fill="#5B91A3" font-weight="700" xml:space="preserve">[04] GITHUB_TELEMETRY.live</text>

  <circle cx="716" cy="26" r="4" fill="{dot_color}">
    <animate attributeName="opacity" values="1;0.25;1" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <text class="mono" x="728" y="30" font-size="11.5" fill="#eeece8" opacity="0.85" xml:space="preserve">{esc(mode_label)} · 6H CRON</text>

  <!-- Left KPI Cards -->
  <rect x="24" y="60" width="132" height="84" rx="4" fill="#111111" stroke="#242424" stroke-width="1"/>
  <text class="mono" x="38" y="84" font-size="11" fill="#5B91A3" xml:space="preserve">REPOS</text>
  <text class="mono" x="38" y="122" font-size="26" font-weight="700" fill="#eeece8" xml:space="preserve">{esc(data["public_repos"])}</text>

  <rect x="168" y="60" width="132" height="84" rx="4" fill="#111111" stroke="#242424" stroke-width="1"/>
  <text class="mono" x="182" y="84" font-size="11" fill="#F25912" xml:space="preserve">STARS</text>
  <text class="mono" x="182" y="122" font-size="26" font-weight="700" fill="#eeece8" xml:space="preserve">{esc(data["stars"])}</text>

  <rect x="312" y="60" width="144" height="84" rx="4" fill="#111111" stroke="#242424" stroke-width="1"/>
  <text class="mono" x="326" y="84" font-size="11" fill="#5B91A3" xml:space="preserve">FOLLOWERS</text>
  <text class="mono" x="326" y="122" font-size="26" font-weight="700" fill="#eeece8" xml:space="preserve">{esc(data["followers"])}</text>

  <!-- Left Bottom Metadata -->
  <rect x="24" y="156" width="432" height="100" rx="4" fill="#111111" stroke="#242424" stroke-width="1"/>
  <text class="mono" x="38" y="180" font-size="11.5" fill="#F25912" font-weight="700" xml:space="preserve">$ git log --summary --languages</text>
  <text class="mono" x="38" y="204" font-size="12" fill="#eeece8" xml:space="preserve">{esc(truncate(data["top_langs"], 52))}</text>
  <text class="mono" x="38" y="236" font-size="11" fill="#eeece8" opacity="0.58" xml:space="preserve">Last sync: {esc(data["synced_at"])}</text>

  <!-- Right Panel: Recent Activity -->
  <rect x="472" y="60" width="404" height="196" rx="4" fill="#111111" stroke="#242424" stroke-width="1"/>
  <text class="mono" x="488" y="84" font-size="11.5" fill="#5B91A3" font-weight="700" xml:space="preserve">├── RECENTLY_PUSHED_REPOS</text>
  <text class="mono" x="488" y="110" font-size="11" fill="#eeece8" opacity="0.55" xml:space="preserve">Auto-refreshed via GitHub Actions workflow</text>
  <line x1="488" y1="124" x2="860" y2="124" stroke="#242424" stroke-width="1"/>
  <text class="mono" x="488" y="152" font-size="11" fill="#eeece8" opacity="0.5" xml:space="preserve">#   REPOSITORY                 STACK            STARS</text>
{recent_block}
  <rect class="pulse" x="488" y="240" width="84" height="3" rx="1.5" fill="#F25912"/>
</svg>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Generate placeholder SVG without calling GitHub API.",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if args.offline:
        data = offline_telemetry()
    else:
        try:
            data = collect_telemetry(USERNAME, token)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"Warning: GitHub API fetch failed ({exc}); using offline fallback.")
            data = offline_telemetry()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_svg(data), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({data['mode']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
