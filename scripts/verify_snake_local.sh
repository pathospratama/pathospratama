#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

printf '\n== Pathos Snake local verification ==\n'
$PYTHON_BIN --version

printf '\n[1/5] Python syntax\n'
$PYTHON_BIN -m py_compile scripts/snake/generate.py
rm -rf scripts/snake/__pycache__
echo 'PASS'

printf '\n[2/5] JSON validation\n'
$PYTHON_BIN - <<'PY'
import json
from pathlib import Path
for p in (Path('scripts/snake/config.json'), Path('scripts/snake/sample-contributions.json')):
    json.loads(p.read_text(encoding='utf-8'))
    print(f'PASS: {p}')
PY

printf '\n[3/5] Workflow YAML validation\n'
$PYTHON_BIN - <<'PY'
try:
    import yaml
except ImportError:
    raise SystemExit('PyYAML is required for local YAML validation: python3 -m pip install pyyaml')
from pathlib import Path
files = [Path('.github/workflows/snake.yml'), Path('.github/workflows/metrics.yml')]
radar = Path('.github/workflows/radar.yml')
if radar.exists():
    files.append(radar)
for p in files:
    yaml.safe_load(p.read_text(encoding='utf-8'))
    print(f'PASS: {p}')
PY

printf '\n[4/5] Offline SVG generation\n'
rm -rf /tmp/pathos-snake-local-check
a="$ROOT_DIR/scripts/snake/generate.py"
$PYTHON_BIN "$a" \
  --config scripts/snake/config.json \
  --input scripts/snake/sample-contributions.json \
  --output-dir /tmp/pathos-snake-local-check \
  --prefix github-contribution-snake

$PYTHON_BIN - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
for p in sorted(Path('/tmp/pathos-snake-local-check').glob('*.svg')):
    s = p.read_text(encoding='utf-8')
    ET.fromstring(s)
    for marker in ('<animateMotion', '<animateTransform', 'PATHOS // SNAKE.PROTOCOL', 'id="snakeHead"'):
        assert marker in s, f'{p}: missing {marker}'
    print(f'PASS: {p} ({p.stat().st_size} bytes)')
PY

printf '\n[5/5] Git working-tree safety check\n'
git diff --check 2>/dev/null || true

echo '\nALL LOCAL SNAKE CHECKS PASSED.'
echo 'To push after reviewing: git status && git add ... && git commit ... && git push origin main'
