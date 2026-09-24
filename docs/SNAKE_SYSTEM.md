# 🐍 Pathos Kratos — Contribution Snake System

This is a repository-owned contribution animation, designed to feel like part of the Pathos Kratos engineering system rather than a generic README widget.

## Visual concept

```text
CONTRIBUTION GRID
      │
      ▼
   SCAN DATA
      │
      ▼
  SNAKE ROUTE
      │
      ├── HEAD finds active cell
      │
      ├── BITE pulse
      │
      ├── CELL shrinks + fades
      │
      ├── BODY follows
      │
      └── CELL respawns next loop
```

### Snake anatomy

- **Head**: gradient lavender/mint/amber, two eyes, mouth line, outer pulse ring.
- **Body**: 18 timed segments; each segment follows the same route with a negative start offset so the body visibly trails the head.
- **Trail**: a low-opacity dashed route reinforces direction without overpowering the contribution graph.
- **Food**: only non-zero contribution cells are animated as targets.
- **Bite effect**: pulse ring + scale down + fade. On the next loop the contribution cell returns.
- **Theme**: separate light and dark SVGs for GitHub's `<picture>` theme switch.

## Runtime architecture

```text
GitHub contribution calendar
          │
          ▼
       GraphQL
          │
          ▼
 scripts/snake/generate.py
          │
          ├── normalize cells
          ├── preserve contribution colors
          ├── build serpentine path
          ├── schedule hit timestamps
          └── render SVG/SMIL animation
          │
          ▼
       dist/*.svg
          │
          ▼
  output branch / GitHub
          │
          ▼
       README.md
```

## Why Python + SVG?

GitHub profile READMEs do not provide a place to run arbitrary JavaScript inside the rendered profile. The animation is therefore emitted as a static SVG document that contains SVG animation primitives. This also makes the renderer deterministic and repository-owned.

## Files

```text
.github/workflows/snake.yml
scripts/snake/
├── config.json
├── generate.py
└── sample-contributions.json
docs/SNAKE_SYSTEM.md
preview.html
```

## Local sample preview

No token or network is required for the included sample:

```bash
python3 scripts/snake/generate.py \
  --input scripts/snake/sample-contributions.json \
  --output-dir assets \
  --prefix snake-preview

open preview.html
```

## Real contribution generation

```bash
export GITHUB_TOKEN="YOUR_TOKEN"
export GITHUB_USER="pathospratama"
python3 scripts/snake/generate.py \
  --config scripts/snake/config.json \
  --output-dir dist \
  --prefix github-contribution-snake
```

The workflow passes `METRICS_TOKEN` when that secret exists and falls back to the built-in Actions token, matching the repository's existing analytics setup.

## Animation tuning

The main values are in `scripts/snake/config.json`:

| Key | Meaning |
| --- | --- |
| `loop_seconds` | Total traversal time for one lap |
| `snake_segments` | Number of visible body segments |
| `segment_gap_seconds` | Delay between body segments |
| `cell_size` | Contribution square size |
| `cell_gap` | Space between squares |
| `accent` | Main snake color |
| `mint` | Secondary body/head color |
| `amber` | Highlight color |

The current Pathos palette is `#AA9BEF`, `#7EE7C7`, and `#F5C77E` on a GitHub-style dark/light surface.

## Workflow

The workflow refreshes every six hours, can be run manually, and reruns when the snake implementation or README changes. The generated SVGs are published into the `output` branch and referenced from the profile README.

## Troubleshooting

### Actions succeeds but the README stays old

GitHub/raw content can be cached. Open the `output` branch and confirm the two SVG files changed, then allow the profile image cache to refresh.

### GraphQL returns an authentication error

Run the generator locally with a valid `GITHUB_TOKEN`. In Actions, verify that `METRICS_TOKEN` exists when the repository relies on it and that the workflow still has `contents: write`.

### The animation is too fast or too slow

Change `loop_seconds`. Keep `segment_gap_seconds` small enough that the tail remains attached visually to the head.
