#!/usr/bin/env python3
# Pathos Kratos — custom contribution snake renderer.
# Standard library only. Generates animated SVG from GitHub GraphQL data.

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.sax.saxutils import escape

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
DEFAULT_CONFIG = Path(__file__).with_name("config.json")


@dataclass(frozen=True)
class Cell:
    x: int
    y: int
    count: int
    color: str
    level: str = "NONE"
    date: str = ""


class SnakeError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SnakeError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SnakeError(f"Invalid JSON in {path}: {exc}") from exc


def load_config(path: Path) -> dict[str, Any]:
    cfg = read_json(path)
    required = (
        "loop_seconds",
        "snake_segments",
        "segment_gap_seconds",
        "cell_size",
        "cell_gap",
        "accent",
    )
    missing = [key for key in required if key not in cfg]
    if missing:
        raise SnakeError(f"config.json missing keys: {', '.join(missing)}")
    return cfg


def fetch_github_calendar(username: str, token: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=371)
    end = now + timedelta(days=1)

    query = """
    query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) {
        contributionsCollection(from:$from, to:$to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
                color
                contributionLevel
              }
            }
          }
        }
      }
    }
    """

    body = json.dumps(
        {
            "query": query,
            "variables": {
                "login": username,
                "from": start.isoformat().replace("+00:00", "Z"),
                "to": end.isoformat().replace("+00:00", "Z"),
            },
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        method="POST",
        headers={
            "Authorization": f"bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "pathos-kratos-contribution-snake",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SnakeError(f"GitHub GraphQL HTTP {exc.code}: {detail[:700]}") from exc
    except urllib.error.URLError as exc:
        raise SnakeError(f"GitHub GraphQL connection failed: {exc.reason}") from exc

    data = json.loads(payload)
    if data.get("errors"):
        msg = "; ".join(item.get("message", "unknown error") for item in data["errors"])
        raise SnakeError(f"GitHub GraphQL error: {msg}")
    return data


def github_cells(payload: dict[str, Any]) -> tuple[list[Cell], int]:
    try:
        calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = calendar["weeks"]
    except (KeyError, TypeError) as exc:
        raise SnakeError("GitHub response does not contain a contribution calendar") from exc

    cells: list[Cell] = []
    for x, week in enumerate(weeks):
        for day in week.get("contributionDays", []):
            color = day.get("color") or "#EBEDF0"
            if not HEX_RE.match(color):
                color = "#EBEDF0"
            cells.append(
                Cell(
                    x=x,
                    y=max(0, min(6, int(day.get("weekday", 0)))),
                    count=int(day.get("contributionCount", 0)),
                    color=color,
                    level=str(day.get("contributionLevel", "NONE")),
                    date=str(day.get("date", "")),
                )
            )
    total = int(calendar.get("totalContributions", sum(c.count for c in cells)))
    return cells, total


def sample_cells(payload: dict[str, Any]) -> tuple[list[Cell], int]:
    cells: list[Cell] = []
    for item in payload.get("cells", []):
        color = item.get("color") or "#39D353"
        if not HEX_RE.match(color):
            color = "#39D353"
        cells.append(
            Cell(
                x=int(item["x"]),
                y=max(0, min(6, int(item["y"]))),
                count=int(item.get("count", 0)),
                color=color,
                level=str(item.get("level", "FOUR_QUARTILE")),
                date=str(item.get("date", "")),
            )
        )
    total = int(payload.get("totalContributions", sum(c.count for c in cells)))
    return cells, total


def grid_and_width(cells: Iterable[Cell]) -> tuple[dict[tuple[int, int], Cell], int]:
    grid: dict[tuple[int, int], Cell] = {}
    max_x = 0
    for cell in cells:
        grid[(cell.x, cell.y)] = cell
        max_x = max(max_x, cell.x)
    return grid, max_x + 1


def serpentine_path(grid: dict[tuple[int, int], Cell], columns: int) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    for x in range(columns):
        ys = range(7) if x % 2 == 0 else range(6, -1, -1)
        for y in ys:
            if (x, y) in grid:
                path.append((x, y))
    if len(path) < 10:
        raise SnakeError("Contribution calendar is unexpectedly small")
    return path


def xml(value: object) -> str:
    return escape(str(value), {'"': '&quot;'})


def sec(value: float) -> str:
    return f"{value:.3f}s"


def number(value: int) -> str:
    return f"{value:,}"


def render_svg(
    cells: list[Cell],
    total: int,
    config: dict[str, Any],
    theme_name: str,
) -> str:
    theme = config[theme_name]
    cell_size = int(config["cell_size"])
    gap = int(config["cell_gap"])
    radius = float(config.get("radius", 2.8))
    loop = float(config["loop_seconds"])
    segments = max(6, int(config["snake_segments"]))
    segment_gap = float(config["segment_gap_seconds"])
    accent = str(config["accent"])
    mint = str(config.get("mint", "#7EE7C7"))
    amber = str(config.get("amber", "#F5C77E"))

    grid, columns = grid_and_width(cells)
    path = serpentine_path(grid, columns)
    step = loop / len(path)
    width = columns * (cell_size + gap) + 24
    height = 7 * (cell_size + gap) + 48

    def point(coord: tuple[int, int]) -> tuple[float, float]:
        x, y = coord
        px = 12 + x * (cell_size + gap) + cell_size / 2
        py = 34 + y * (cell_size + gap) + cell_size / 2
        return px, py

    path_d = " ".join(
        f"{'M' if index == 0 else 'L'} {point(coord)[0]:.2f} {point(coord)[1]:.2f}"
        for index, coord in enumerate(path)
    )

    out: list[str] = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="title desc">'
    )
    out.append("<title id=\"title\">Pathos Kratos contribution snake</title>")
    out.append(
        '<desc id="desc">A repository-generated snake follows the GitHub contribution '
        'calendar and eats active contribution cells.</desc>'
    )
    out.append(
        f'''<defs>
  <filter id="glow" x="-300%" y="-300%" width="600%" height="600%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="soft" x="-200%" y="-200%" width="400%" height="400%">
    <feGaussianBlur stdDeviation="1.35" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="snakeGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{accent}"/>
    <stop offset="65%" stop-color="{mint}"/>
    <stop offset="100%" stop-color="{amber}"/>
  </linearGradient>
  <linearGradient id="headGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#FFFFFF"/>
    <stop offset="15%" stop-color="{mint}"/>
    <stop offset="55%" stop-color="{accent}"/>
    <stop offset="100%" stop-color="{amber}"/>
  </linearGradient>
  <path id="snakePath" d="{xml(path_d)}" fill="none"/>
</defs>'''
    )
    out.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="14" fill="{theme["background"]}"/>'
    )
    out.append(
        f'<rect x="7" y="7" width="{width-14}" height="{height-14}" rx="11" '
        f'fill="none" stroke="{theme["border"]}" stroke-opacity="0.72"/>'
    )
    out.append(
        f'<text x="14" y="20" fill="{accent}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="7.5" font-weight="700" letter-spacing="1.15">PATHOS // SNAKE.PROTOCOL</text>'
    )
    out.append(
        f'<text x="{width-14}" y="20" text-anchor="end" fill="{theme["muted"]}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="7.5" '
        f'letter-spacing="0.85">CONTRIBUTIONS {xml(number(total))}</text>'
    )

    # Small status rail behind the grid.
    out.append(
        f'<rect x="12" y="27" width="{width-24}" height="2" rx="1" fill="{theme["panel"]}"/>'
    )

    # Contribution cells. Only non-zero cells are animated: they are the food.
    for key, cell in sorted(grid.items(), key=lambda item: (item[0][0], item[0][1])):
        cx, cy = point(key)
        active = cell.count > 0
        fill = cell.color if active else theme["empty"]
        opacity = "0.97" if active else "0.66"
        if not active:
            out.append(
                f'<rect x="{cx-cell_size/2:.2f}" y="{cy-cell_size/2:.2f}" width="{cell_size}" '
                f'height="{cell_size}" rx="{radius}" fill="{fill}" opacity="{opacity}"/>'
            )
            continue

        hit = path.index(key) * step
        hit_s = sec(hit)
        out.append(
            f'''<g transform="translate({cx:.2f} {cy:.2f})">
  <rect x="{-cell_size/2:.2f}" y="{-cell_size/2:.2f}" width="{cell_size}" height="{cell_size}" rx="{radius}"
        fill="{fill}" opacity="{opacity}" filter="url(#soft)">
    <animateTransform attributeName="transform" type="scale" begin="{hit_s}" dur="{sec(loop)}"
      repeatCount="indefinite" values="1;1.25;0.68;0.68;1" keyTimes="0;0.025;0.07;0.91;0.96"/>
    <animate attributeName="opacity" begin="{hit_s}" dur="{sec(loop)}" repeatCount="indefinite"
      values="{opacity};1;0.22;0.22;{opacity}" keyTimes="0;0.025;0.09;0.91;0.96"/>
  </rect>
  <circle r="2.1" fill="none" stroke="{accent}" stroke-width="0.85" opacity="0">
    <animate attributeName="r" begin="{hit_s}" dur="{sec(loop)}" repeatCount="indefinite"
      values="2.1;7.4;7.4;2.1" keyTimes="0;0.06;0.91;0.96"/>
    <animate attributeName="opacity" begin="{hit_s}" dur="{sec(loop)}" repeatCount="indefinite"
      values="0;0.75;0;0" keyTimes="0;0.05;0.13;1"/>
  </circle>
</g>'''
        )

    out.append(
        f'''<path d="{xml(path_d)}" fill="none" stroke="{accent}" stroke-width="1.2" stroke-linecap="round"
      stroke-linejoin="round" stroke-dasharray="2 9" opacity="0.18">
  <animate attributeName="stroke-dashoffset" values="0;-44" dur="2.8s" repeatCount="indefinite"/>
</path>'''
    )

    # Body segments. Negative begin values create a trailing snake effect.
    for index in range(segments - 1, 0, -1):
        delay = index * segment_gap
        r = max(2.45, 5.8 - index * 0.21)
        opacity = max(0.13, 0.90 - index * 0.045)
        filt = "url(#glow)" if index <= 3 else "url(#soft)"
        out.append(
            f'''<circle r="{r:.2f}" fill="url(#snakeGradient)" opacity="{opacity:.3f}" filter="{filt}">
  <animateMotion dur="{loop:.3f}s" begin="-{delay:.3f}s" repeatCount="indefinite" rotate="auto" calcMode="linear">
    <mpath href="#snakePath" xlink:href="#snakePath"/>
  </animateMotion>
</circle>'''
        )

    out.append(
        f'''<g id="snakeHead" filter="url(#glow)">
  <circle r="7.5" fill="url(#headGradient)" stroke="{theme["background"]}" stroke-width="1.2"/>
  <circle cx="-2.25" cy="-2.35" r="1.12" fill="{theme["background"]}"/>
  <circle cx="2.25" cy="-2.35" r="1.12" fill="{theme["background"]}"/>
  <circle cx="-2.25" cy="-2.35" r="0.40" fill="#FFFFFF"/>
  <circle cx="2.25" cy="-2.35" r="0.40" fill="#FFFFFF"/>
  <path d="M -2.8 1.55 Q 0 3.3 2.8 1.55" fill="none" stroke="{theme["background"]}" stroke-width="0.9" stroke-linecap="round"/>
  <circle r="9.5" fill="none" stroke="{accent}" stroke-width="0.7" opacity="0.46">
    <animate attributeName="r" values="8.7;11.5;8.7" dur="1.7s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.5;0.04;0.5" dur="1.7s" repeatCount="indefinite"/>
  </circle>
  <animateMotion dur="{loop:.3f}s" repeatCount="indefinite" rotate="auto" calcMode="linear">
    <mpath href="#snakePath" xlink:href="#snakePath"/>
  </animateMotion>
</g>'''
    )

    out.append(
        f'''<text x="14" y="{height-13}" fill="{theme["muted"]}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
      font-size="6.7" letter-spacing="0.75">SCAN → ACQUIRE → BITE → CONSUME → REPEAT</text>'''
    )
    out.append(
        f'''<text x="{width-14}" y="{height-13}" text-anchor="end" fill="{accent}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
      font-size="6.7" font-weight="700" letter-spacing="0.75">PATHOS / LIVE CONTRIBUTION FEED</text>'''
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def write_outputs(cells: list[Cell], total: int, config: dict[str, Any], output_dir: Path, prefix: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        target = output_dir / f"{prefix}-{theme}.svg"
        target.write_text(render_svg(cells, total, config, theme), encoding="utf-8")
        print(f"wrote {target} ({target.stat().st_size} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Pathos Kratos contribution snake SVG")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, help="offline data JSON; bypasses GitHub API")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--prefix", default="github-contribution-snake")
    parser.add_argument("--username", default=os.getenv("GITHUB_USER", "pathospratama"))
    args = parser.parse_args()

    config = load_config(args.config)
    if args.input:
        cells, total = sample_cells(read_json(args.input))
        print("source: offline sample")
    else:
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not token:
            raise SnakeError("GITHUB_TOKEN is required unless --input is used")
        cells, total = github_cells(fetch_github_calendar(args.username, token))
        print(f"source: GitHub contribution calendar for @{args.username}")

    if not cells:
        raise SnakeError("No contribution cells returned")

    print(f"cells: {len(cells)} | total contributions: {total}")
    write_outputs(cells, total, config, args.output_dir, args.prefix)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SnakeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
