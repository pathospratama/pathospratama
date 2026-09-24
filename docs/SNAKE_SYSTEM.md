# 🐍 Pathos Kratos — Contribution Snake System

The live profile uses `Platane/snk/svg-only@v3` for the contribution-grid animation. The upstream action supports a GitHub username, a token input, custom snake color, and a five-color contribution palette. The repository keeps its own README presentation and output branch.

## Runtime flow

```text
GitHub contribution calendar
          │
          ▼
   Platane/snk svg-only
          │
          ├── light SVG
          └── dark SVG
          │
          ▼
   output branch publisher
          │
          ▼
       README.md
```

## Pathos visual system

```text
SNAKE       #AA9BEF  lavender
SECONDARY   #7EE7C7  mint
HIGHLIGHT   #F5C77E  amber
DARK BG     #0D1117
aPANEL      #161B22
MUTED       #8B949E
```

The live Snake workflow uses the exact output names already referenced by the profile:

```text
output/github-contribution-snake-light.svg
output/github-contribution-snake-dark.svg
```

## Why the previous Metrics job failed

The `lowlighter/metrics` action requires its `token` input, and its current documentation describes that input as a GitHub Personal Access Token. Your failing run showed the token was missing, so the action stopped before generating the language SVG.

This update removes that external PAT dependency from the language breakdown. `scripts/language_card.py` reads public repository language byte counts through the GitHub REST API and renders `assets/metrics.languages.svg` inside the repository itself.

## Metrics flow

```text
public repository language stats
            │
            ▼
 scripts/language_card.py
            │
            ▼
assets/metrics.languages.svg
            │
            ▼
         README
```

## Local validation

```bash
chmod +x scripts/verify_snake_local.sh
./scripts/verify_snake_local.sh
```

The check validates Python syntax, JSON, YAML, the custom offline snake renderer, the self-hosted language card, shell syntax, and whitespace errors.

## Offline previews

Custom renderer:

```bash
python3 scripts/snake/generate.py \
  --config scripts/snake/config.json \
  --input scripts/snake/sample-contributions.json \
  --output-dir /tmp/pathos-snake-check \
  --prefix github-contribution-snake
```

Language card:

```bash
python3 scripts/language_card.py \
  --user pathospratama \
  --input scripts/language-sample.json \
  --output /tmp/pathos-language-card.svg
```

## GitHub permissions

The Snake job uses `contents: write` at the job level because it publishes generated SVGs to `output`. The GitHub Actions permission model supports this job-level setting.

For the repository, check:

`Settings → Actions → General → Workflow permissions`

The workflow must be allowed to write repository contents.
