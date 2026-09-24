#!/usr/bin/env python3
"""Generate a Pathos-styled, repository-owned GitHub language card."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FONT = "ui-sans-serif,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"
ACCENT = "#AA9BEF"
MINT = "#7EE7C7"
AMBER = "#F5C77E"
BG = "#0D1117"
PANEL = "#161B22"
BORDER = "#30363D"
TEXT = "#E6EDF3"
MUTED = "#8B949E"

COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A",
    "HTML": "#E34C26", "CSS": "#563D7C", "Shell": "#89E051", "Rust": "#DEA584",
    "Go": "#00ADD8", "C++": "#F34B7D", "C": "#555555", "Java": "#B07219",
    "PHP": "#4F5D95", "Ruby": "#701516", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "Dart": "#00B4AB", "Vue": "#41B883", "Svelte": "#FF3E00",
    "Jupyter Notebook": "#DA5B0B",
}


def esc(value: object) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def get_json(url: str, token: str | None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pathos-kratos-language-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def collect_languages(user: str, token: str | None) -> dict[str, int]:
    totals: dict[str, int] = {}
    page = 1
    encoded = urllib.parse.quote(user, safe="")

    while True:
        repos_url = (
            f"https://api.github.com/users/{encoded}/repos"
            f"?per_page=100&page={page}&type=owner&sort=pushed"
        )
        repos = get_json(repos_url, token)
        if not repos:
            break

        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            try:
                languages = get_json(repo["languages_url"], token)
            except (urllib.error.HTTPError, urllib.error.URLError):
                continue
            for name, count in languages.items():
                totals[name] = totals.get(name, 0) + int(count)

        if len(repos) < 100:
            break
        page += 1

    return totals


def render(data: dict[str, int], user: str, width: int = 760, height: int = 230) -> str:
    items = [(name, int(value)) for name, value in data.items() if int(value) > 0]
    items.sort(key=lambda item: item[1], reverse=True)
    items = items[:8]
    if not items:
        raise RuntimeError("No language data available")

    total = sum(value for _, value in items)
    bar_x, bar_y = 24, 86
    bar_w, bar_h = width - 48, 14
    bar_parts: list[str] = []
    cursor = float(bar_x)

    for index, (name, value) in enumerate(items):
        segment = bar_w - (len(items) * 2) if index == len(items) - 1 else (value / total) * bar_w
        segment = max(2.0, segment)
        bar_parts.append(
            f'<rect x="{cursor:.2f}" y="{bar_y}" width="{segment:.2f}" '
            f'height="{bar_h}" rx="4" fill="{COLORS.get(name, ACCENT)}"/>'
        )
        cursor += segment

    rows: list[str] = []
    col_w = (width - 48) / 2
    for i, (name, value) in enumerate(items):
        col = i % 2
        row = i // 2
        x = 24 + col * col_w
        y = 132 + row * 22
        pct = value / total * 100
        dot = COLORS.get(name, ACCENT)
        rows.append(
            f'<circle cx="{x + 5:.1f}" cy="{y - 4:.1f}" r="5" fill="{dot}"/>'
            f'<text x="{x + 17:.1f}" y="{y:.1f}" font-size="11.5" fill="{TEXT}">{esc(name)}</text>'
            f'<text x="{x + col_w - 20:.1f}" y="{y:.1f}" text-anchor="end" '
            f'font-size="11.5" fill="{MUTED}">{pct:.1f}%</text>'
        )

    subtitle = f"{len(items)} leading languages · repository-owned analytics"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(user)} language breakdown" font-family="{FONT}">
  <defs>
    <linearGradient id="pathosGradient" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="{ACCENT}"/>
      <stop offset="0.55" stop-color="{MINT}"/>
      <stop offset="1" stop-color="{AMBER}"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="{BG}" stroke="{BORDER}"/>
  <text x="24" y="31" font-size="16" font-weight="700" fill="{TEXT}">Technology Mix</text>
  <text x="24" y="51" font-size="11" fill="{MUTED}">{esc(user)} · {esc(subtitle)}</text>
  <rect x="24" y="75" width="{width - 48}" height="2" rx="1" fill="url(#pathosGradient)" opacity="0.72"/>
  <rect x="24" y="86" width="{width - 48}" height="14" rx="4" fill="{PANEL}"/>
  {''.join(bar_parts)}
  {''.join(rows)}
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="pathospratama")
    parser.add_argument("--output", type=Path, default=Path("assets/metrics.languages.svg"))
    parser.add_argument("--input", type=Path, help="Offline JSON language-byte map")
    args = parser.parse_args()

    if args.input:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        try:
            data = collect_languages(args.user, token)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"GitHub API HTTP {exc.code}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"GitHub API connection failed: {exc.reason}") from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(data, args.user), encoding="utf-8")
    print(f"wrote {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
