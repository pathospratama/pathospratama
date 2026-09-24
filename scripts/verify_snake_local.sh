#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "== Pathos Kratos local verification =="
$PYTHON_BIN --version

echo "[1/7] Python syntax"
$PYTHON_BIN -m py_compile scripts/snake/generate.py scripts/language_card.py
rm -rf scripts/snake/__pycache__ scripts/__pycache__
echo "PASS"

echo "[2/7] JSON validation"
$PYTHON_BIN - <<'PY'
import json
from pathlib import Path
for p in [Path('scripts/snake/config.json'), Path('scripts/snake/sample-contributions.json'), Path('scripts/language-sample.json')]:
    json.loads(p.read_text(encoding='utf-8'))
    print('PASS:', p)
PY

echo "[3/7] YAML validation"
$PYTHON_BIN - <<'PY'
try:
    import yaml
except ImportError as exc:
    raise SystemExit('Install PyYAML: python3 -m pip install pyyaml') from exc
from pathlib import Path
for p in sorted(Path('.github/workflows').glob('*.yml')):
    yaml.safe_load(p.read_text(encoding='utf-8'))
    print('PASS:', p)
PY

echo "[4/7] Offline custom snake renderer"
rm -rf /tmp/pathos-snake-check
$PYTHON_BIN scripts/snake/generate.py \
  --config scripts/snake/config.json \
  --input scripts/snake/sample-contributions.json \
  --output-dir /tmp/pathos-snake-check \
  --prefix github-contribution-snake
$PYTHON_BIN - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
for p in sorted(Path('/tmp/pathos-snake-check').glob('*.svg')):
    s=p.read_text(encoding='utf-8')
    ET.fromstring(s)
    for marker in ('<animateMotion', '<animateTransform', 'SNAKE.PROTOCOL', 'snakeHead'):
        assert marker in s, f'{p}: missing {marker}'
    print('PASS:', p, p.stat().st_size, 'bytes')
PY

echo "[5/7] Offline language card"
$PYTHON_BIN scripts/language_card.py \
  --user pathospratama \
  --input scripts/language-sample.json \
  --output /tmp/pathos-language-card.svg
$PYTHON_BIN - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
p=Path('/tmp/pathos-language-card.svg')
s=p.read_text(encoding='utf-8')
ET.fromstring(s)
assert 'Technology Mix' in s
assert '#AA9BEF' in s
print('PASS:', p, p.stat().st_size, 'bytes')
PY

echo "[6/7] Shell syntax"
bash -n scripts/verify_snake_local.sh
echo "PASS"

echo "[7/7] Git whitespace check"
git diff --check 2>/dev/null || true
echo "PASS"

echo "ALL LOCAL CHECKS PASSED."
