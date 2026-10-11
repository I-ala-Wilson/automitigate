"""The demo entry point and the Qollab bundle."""
import io
import sys
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_replay_runs_and_recommends(monkeypatch):
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    monkeypatch.setattr(plt, "show", lambda: None)
    monkeypatch.chdir(ROOT)
    import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        main.main(circuit="ghz4", source="ibm", learner="eps-greedy", replays=2, live=False)
    out = buf.getvalue()
    assert "Recommendation after 240 pulls" in out
    assert "pseudo-regret" in out


def test_qollab_bundle_is_complete():
    zp = ROOT / "qollab_project.zip"
    assert zp.exists()
    names = set(zipfile.ZipFile(zp).namelist())
    for f in ("main.py", "README.md", "automitigate/learners.py", "automitigate/arms.py",
              "automitigate/forward.py", "automitigate/score.py", "data/replay/summary.json"):
        assert f in names, f
    assert sum(n.startswith("data/replay/") and n.endswith(".json") for n in names) == 15
