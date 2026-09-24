#!/usr/bin/env python3

from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "emmi-lili"

SOURCE_ENGINE = ORIGINAL / "scripts/banner/generate.py"
TARGET_ENGINE = ROOT / "scripts/banner/generate.py"

SOURCE_BANNER_DIR = ORIGINAL / "scripts/banner"
TARGET_BANNER_DIR = ROOT / "scripts/banner"

BACKUP = ROOT / ".backup-engine" / datetime.now().strftime("%Y%m%d-%H%M%S")


def fail(message: str) -> None:
    raise SystemExit(f"\n❌ {message}\n")


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def backup_file(src: Path) -> None:
    if src.exists():
        rel = src.relative_to(ROOT)
        dst = BACKUP / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def backup_dir(src: Path) -> None:
    if src.exists():
        rel = src.relative_to(ROOT)
        dst = BACKUP / rel
        shutil.copytree(src, dst)


# ---------------------------------------------------------------------
# Validate local sibling clone
# ---------------------------------------------------------------------

if not ORIGINAL.exists():
    fail(
        f"Original clone tidak ditemukan:\n{ORIGINAL}\n\n"
        "Struktur yang dibutuhkan:\n"
        "README/\n"
        "├── emmi-lili/\n"
        "└── Pathos/\n"
    )

if not SOURCE_ENGINE.exists():
    fail(f"generate.py asli tidak ditemukan:\n{SOURCE_ENGINE}")

if not (ORIGINAL / "assets/source/mrr.png").exists():
    fail("mrr.png pada clone asli tidak ditemukan.")

if not (ROOT / "assets/source/mrr.png").exists():
    fail("mrr.png pada Pathos tidak ditemukan.")


# ---------------------------------------------------------------------
# Backup current Pathos engine
# ---------------------------------------------------------------------

BACKUP.mkdir(parents=True, exist_ok=True)

for path in [
    ROOT / "scripts/banner/generate.py",
    ROOT / "scripts/banner/requirements.txt",
]:
    backup_file(path)

backup_dir(ROOT / "scripts/banner/data")
backup_dir(ROOT / "scripts/banner/logos")

print(f"\n📦 Backup dibuat di:\n{BACKUP}\n")


# ---------------------------------------------------------------------
# Verify mrr.png hashes
# ---------------------------------------------------------------------

def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


original_hash = sha256(ORIGINAL / "assets/source/mrr.png")
pathos_hash = sha256(ROOT / "assets/source/mrr.png")

print("Original mrr.png SHA256 :", original_hash)
print("Pathos   mrr.png SHA256 :", pathos_hash)

if original_hash == pathos_hash:
    print("✅ mrr.png IDENTIK dengan clone asli.\n")
else:
    print("⚠️ mrr.png berbeda. Tetap mempertahankan mrr.png milik Pathos.\n")


# ---------------------------------------------------------------------
# Copy EXACT engine/assets from original clone
# ---------------------------------------------------------------------

TARGET_ENGINE.parent.mkdir(parents=True, exist_ok=True)

shutil.copy2(
    SOURCE_ENGINE,
    TARGET_ENGINE,
)

original_requirements = SOURCE_BANNER_DIR / "requirements.txt"
target_requirements = TARGET_BANNER_DIR / "requirements.txt"

if original_requirements.exists():
    shutil.copy2(
        original_requirements,
        target_requirements,
    )

# Replace generated engine data and generated logos with the originals.
for name in ("data", "logos"):
    src = SOURCE_BANNER_DIR / name
    dst = TARGET_BANNER_DIR / name

    if src.exists():
        if dst.exists():
            shutil.rmtree(dst)

        shutil.copytree(src, dst)


print("✅ Original banner engine copied from clone.\n")


# ---------------------------------------------------------------------
# Patch ONLY identity/profile text.
# Do NOT modify the animation algorithm.
# ---------------------------------------------------------------------

engine = TARGET_ENGINE.read_text(encoding="utf-8")


PATHOS_ROWS = """ROWS = [
    ("Subject", "Pathos Kratos"),
    ("Role", "Senior Developer · IT Consultant"),
    ("Origin", "Indonesia"),
    ("Education", "Software Engineering · Self-Taught"),
    ("Status", "Building + Learning + Shipping"),
    ("ToolChain", "VS Code · Cursor · Git · GitHub"),
    ("Core.Lang", "Python · TypeScript · JavaScript · SQL"),
    ("Core.Frontend", "React · Next.js · Three.js · Tailwind"),
    ("Core.Backend", "FastAPI · Flask · Node.js"),
    ("Core.Database", "PostgreSQL · Supabase · Firebase"),
    ("Core.Infra", "Docker · Vercel · AWS · Linux"),
    ("Core.AI", "Gemini · Computer Vision · AI Integration"),
    ("Core.IoT", "ESP32 · WebSocket · Bluetooth · IoT Systems"),
    ("Core.3D", "Three.js · React Three Fiber · Blender"),
    ("Core.System", "REST API · WebSocket · Authentication · Realtime"),
    ("Grid.Mail", "—"),
    ("Grid.LinkedIn", "—"),
    ("Grid.GitHub", "@pathospratama"),
    ("Grid.X", "—"),
]"""


engine, count = re.subn(
    r"ROWS\s*=\s*\[.*?\n\]",
    PATHOS_ROWS,
    engine,
    count=1,
    flags=re.S,
)

if count != 1:
    fail("Blok ROWS pada original generate.py tidak ditemukan.")


# Identity-only replacements.
identity_replacements = {
    "Emmi's live system profile":
        "Pathos Kratos live system profile",

    "@emmi-lili":
        "@pathospratama",

    "emmi-lili":
        "pathospratama",

    "UTC-4 · LATAM NODE":
        "UTC+7 · INDONESIA NODE",
}


for old, new in identity_replacements.items():
    engine = engine.replace(old, new)


TARGET_ENGINE.write_text(engine, encoding="utf-8")


# ---------------------------------------------------------------------
# Validate that animation internals are still present.
# ---------------------------------------------------------------------

required_markers = [
    "portrait_points",
    "sample_logo_points",
    "transport",
    "linear_sum_assignment",
    "cdist",
    "TRAVELLER_COUNT = 900",
    "LOOP_SECONDS = 14.2",
    "rust",
    "code",
    "stellar",
]

missing = [
    marker
    for marker in required_markers
    if marker not in engine
]

if missing:
    fail(
        "Engine validation gagal. Marker berikut hilang:\n"
        + "\n".join(f"- {m}" for m in missing)
    )

print("✅ Engine validation passed.")
print("✅ Animation algorithm preserved.")
print("✅ Rust / Code / Stellar morph preserved.")
print("✅ Only profile identity was changed.\n")


print("Sekarang jalankan:")
print()
print("python3 scripts/banner/generate.py")
print()
print("Kemudian:")
print()
print("open preview.html")
print()