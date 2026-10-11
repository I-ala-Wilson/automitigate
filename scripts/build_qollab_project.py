"""Assemble the Qollab upload bundle (<= 100 files, <= 2 MB each) from the repo.

  python scripts/build_qollab_project.py   # -> qollab_project/ and qollab_project.zip

Drag qollab_project.zip onto the Qollab "Upload your own files" card (or into the file
tree of the existing project). README.md becomes the project write-up automatically.
"""
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qollab_project"
ZIP = ROOT / "qollab_project.zip"
MAX_FILE = 2_000_000
MAX_FILES = 100

ALWAYS = ["main.py", "README.md", "LICENSE", "requirements.txt",
          "automitigate/__init__.py", "automitigate/learners.py", "automitigate/arms.py",
          "automitigate/circuits.py", "automitigate/score.py", "automitigate/forward.py",
          "docs/analysis_plan.md", "docs/results.md", "docs/project_card.md"]
GLOBS = ["data/replay/*.json", "figures/*.png"]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    files = [ROOT / f for f in ALWAYS if (ROOT / f).exists()]
    for g in GLOBS:
        files += sorted(ROOT.glob(g))
    kept, skipped = [], []
    for f in files:
        if f.stat().st_size > MAX_FILE:
            skipped.append((str(f.relative_to(ROOT)), f.stat().st_size))
            continue
        if len(kept) >= MAX_FILES:
            skipped.append((str(f.relative_to(ROOT)), "file limit"))
            continue
        dest = OUT / f.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, dest)
        kept.append(f.relative_to(ROOT))
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in kept:
            z.write(OUT / rel, str(rel))
    total = sum((OUT / r).stat().st_size for r in kept)
    print(f"qollab bundle: {len(kept)} files, {total / 1e6:.1f} MB -> {ZIP.name}")
    for s in skipped:
        print("  skipped:", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
