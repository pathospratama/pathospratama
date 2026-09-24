# Pathos Snake — Local → GitHub Deployment

## 1. Backup the repository

```bash
git status
git branch backup-before-snake-fix
git fetch origin
git pull --rebase origin main
```

If `backup-before-snake-fix` already exists, keep it and continue.

## 2. Apply the update

Copy the contents of this package's `pathospratama/` directory over the profile repository.

Do not remove existing `assets/banner-*`, `assets/radar-*`, `assets/card-*`, or the existing source assets.

## 3. Run local verification

```bash
chmod +x scripts/verify_snake_local.sh
./scripts/verify_snake_local.sh
```

## 4. Review the exact changes

```bash
git diff --check
git status
git diff -- .github/workflows/snake.yml .github/workflows/metrics.yml README.md scripts/language_card.py
```

## 5. Commit and push

```bash
git add README.md \
  .github/workflows/snake.yml \
  .github/workflows/metrics.yml \
  scripts/language_card.py \
  scripts/language-sample.json \
  scripts/verify_snake_local.sh \
  docs/SNAKE_SYSTEM.md \
  docs/SNAKE_SETUP.md

git diff --cached --check
git commit -m "fix: stabilize metrics and pathos snake"
git push origin main
```

## 6. Run the two workflows

After the push:

```text
GitHub → Actions → Generate Pathos Contribution Snake → Run workflow
GitHub → Actions → Metrics → Run workflow
```

## 7. Confirm output branch

The Snake workflow must publish:

```text
output/github-contribution-snake-light.svg
output/github-contribution-snake-dark.svg
```

The README is already wired to those exact files.
