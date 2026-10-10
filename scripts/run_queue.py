"""The experiment queue. One process per laptop, started once, runs until Sunday 09:00 ET.

  python -u scripts/run_queue.py --laptop ian|thomas [--until 2026-10-11T09:00] [--dry-run]

Every loop: git pull --rebase; find the first stage whose inputs exist and whose marker is
missing; run it as a subprocess (one terminal line per minute); on success write the
marker, gzip the pass file, commit and push data/, figures/, docs/results.md, STATUS.md;
on any exception append a `blocked:` block to STATUS.md, push, sleep 5 min, carry on.
Heartbeat data/heartbeat_<laptop>.txt every 30 min. Exit code 3 = finished (the wrapper
scripts stop restarting on 3).
"""
import argparse
import datetime as dt
import gzip
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
PY = sys.executable
DATA = ROOT / "data"
QDIR = DATA / "queue"
STATUS = ROOT / "STATUS.md"

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:  # no tz database (bare Windows): fall back to the local clock
    ET = None

MAC_CIRCUITS = ["ghz4", "ghz8", "grover3"]  # measured 0.3 / 1.4 / 1.5 s per day-cell on the Mac
YOGA_CIRCUITS = ["qft3", "qaoa6"]  # 0.5 / 3.2 s per day-cell on the Mac; the Yoga is slower
MAX_SEEDS = 20
PASS_BUDGET_H = 2.0  # a pass slower than this drops the ladder one rung
GRID = "--p 0,0.01,0.03,0.1 --theta 0,0.05,0.15,0.3 --r 0,0.02"


def now_et():
    return dt.datetime.now(ET) if ET else dt.datetime.now()


def stamp():
    return now_et().strftime("%Y-%m-%d %H:%M ET")


def parse_et(s):
    d = dt.datetime.fromisoformat(s)
    return d.replace(tzinfo=ET) if ET and d.tzinfo is None else d


def sh(cmd, check=True, capture=True):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> {r.returncode}\n{(r.stderr or r.stdout)[-2000:]}")
    return r


def e0_fitted():
    p = DATA / "e0.json"
    if not p.exists():
        return False
    try:
        return bool(json.loads(p.read_text()).get("p2q_fit"))
    except Exception:
        return False


def ab():
    p = DATA / "calib" / "ab.json"
    return json.loads(p.read_text()) if p.exists() else None


class Queue:
    def __init__(self, a):
        self.a = a
        self.laptop = a.laptop
        self.tag = f"[{self.laptop}]"
        self.until = parse_et(a.until)
        self.last_push = None
        self.last_heartbeat = 0.0
        self.line = ""
        self.pass_durations = []
        self.max_seeds = MAX_SEEDS
        self.rungs = []
        QDIR.mkdir(parents=True, exist_ok=True)
        (DATA / "ibm").mkdir(exist_ok=True)
        (DATA / "calib").mkdir(exist_ok=True)

    # ---------------------------------------------------------------- stages
    def marker(self, name):
        return QDIR / f"{self.laptop}_{name}.done"

    def done(self, name):
        return self.marker(name).exists()

    def pass_done(self, laptop, k):
        return (QDIR / f"{laptop}_Q2_seed{k}.done").exists()

    def circuits_for_pass(self, k):
        base = MAC_CIRCUITS if self.laptop == "ian" else YOGA_CIRCUITS
        base = [c for c in base + self.a.also if c not in self.a.skip]
        for rung in self.rungs:
            if rung == "ghz8_5" and k >= 5:
                base = [c for c in base if c != "ghz8"]
            if rung == "drop_qaoa6":
                base = [c for c in base if c != "qaoa6"]
        return base

    def stages(self):
        """Ordered list of (name, inputs_ok, argv list or callable)."""
        L = self.laptop
        S = []
        sweep = [PY, "-u", "scripts/sweep.py"]
        have_nm = (ROOT / "automitigate" / "noise_model.py").exists()
        have_plan = (ROOT / "docs" / "analysis_plan.md").exists()
        have_daily = (DATA / "calibration_daily_fez.parquet").exists()
        have_analysis = (ROOT / "scripts" / "analysis.py").exists()
        have_fwd = (ROOT / "automitigate" / "forward.py").exists()
        late = now_et() > parse_et("2026-10-09T23:00")
        if L == "ian":
            S.append(("Q1", e0_fitted() or late,
                      sweep + ["--source", "static", "--circuits", "ghz4,qft3,grover3", *GRID.split(),
                               "--seeds", "0-4", "--laptop", L, "--out", "data/calib/grid.jsonl"],
                      lambda: sh([PY, "scripts/pick_ab.py"])))
            S.append(("Q1b", self.done("Q1") and ab() is not None and (e0_fitted() or late),
                      sweep + ["--source", "ionq_like", "--circuits", "ghz4,qft3,grover3", "--schedule",
                               "stable,slow,jump", "--seeds", "0-4", "--steps", "300", "--laptop", L,
                               "--out", "data/ionq_like/table.jsonl"], None))
        ibm_ok = have_nm and have_plan and have_daily
        for k in range(self.max_seeds):
            circs = self.circuits_for_pass(k)
            if not circs:
                continue
            S.append((f"Q2_seed{k}", ibm_ok and self.pass_allowed(k),
                      sweep + ["--source", "ibm", "--circuits", ",".join(circs), "--seeds", str(k),
                               "--laptop", L, "--out", f"data/ibm/{L}_seed{k}.jsonl"],
                      lambda k=k: self.gzip_pass(k)))
            if L == "ian":
                n_passes = sum(1 for j in range(k + 1) if self.pass_done("ian", j))
                S.append((f"Q3_after{k}", have_analysis and self.pass_done("ian", k),
                          [PY, "-u", "scripts/analysis.py", "all"], None))
                if k == 2:
                    A = (ab() or {}).get("A", {"p": 0, "theta": 0, "r": 0})
                    S.append(("Q4", self.pass_done("ian", 2) and ab() is not None,
                              sweep + ["--source", "static", "--circuits", "ghz4,qft3", "--shots", "600,1200,2400",
                                       "--seeds", "0-4", "--p", str(A["p"]), "--theta", str(A["theta"]),
                                       "--r", str(A["r"]), "--laptop", L, "--out", "data/calib/shots.jsonl"], None))
            if L == "thomas":
                if k == 5:
                    S.append(("Q2b", have_fwd and ibm_ok and self.pass_done("thomas", 5),
                              sweep + ["--source", "ibm", "--forward", "--circuits", "ghz4,qft3,grover3",
                                       "--seeds", "0-4", "--laptop", L, "--out", "data/ibm/thomas_forward.jsonl"], None))
                if k == 10:
                    S.append(("Q6a", ibm_ok and self.pass_done("thomas", 10),
                              sweep + ["--source", "ibm", "--f", "0.3", "--circuits", "ghz4,qft3", "--seeds", "0-9",
                                       "--laptop", L, "--out", "data/ibm/thomas_f03.jsonl"], None))
                    S.append(("Q6b", ibm_ok and self.pass_done("thomas", 10),
                              sweep + ["--source", "ibm", "--chain-rank", "median", "--circuits", "ghz4", "--seeds", "0-4",
                                       "--laptop", L, "--out", "data/ibm/thomas_median.jsonl"], None))
        if L == "ian":
            S.append(("Q5", have_analysis and now_et() >= parse_et("2026-10-11T09:00"),
                      [PY, "-u", "scripts/analysis.py", "all", "--final"], None))
        return S

    def pass_allowed(self, k):
        """The ladder: never start a pass that cannot finish by Sun 07:30."""
        if self.pass_durations:
            est = max(self.pass_durations[-3:])
            if now_et() + dt.timedelta(seconds=est) > parse_et("2026-10-11T07:30"):
                return False
        return True

    def gzip_file(self, src):
        src = Path(src)
        if src.exists() and src.suffix == ".jsonl":
            with open(src, "rb") as fi, gzip.open(str(src) + ".gz", "wb") as fo:
                shutil.copyfileobj(fi, fo)
            src.unlink()

    def gzip_pass(self, k):
        self.gzip_file(DATA / "ibm" / f"{self.laptop}_seed{k}.jsonl")

    # ---------------------------------------------------------------- git
    def git_sync(self, light=False):
        """Commit what the queue produced (light = heartbeat + STATUS only), pull --rebase, push."""
        if light:
            sh(["git", "add", "-A", "STATUS.md", f"data/heartbeat_{self.laptop}.txt"], check=False)
        else:
            sh(["git", "add", "-A", "data", "STATUS.md"], check=False)
            for extra in ("figures", "docs/results.md"):
                if (ROOT / extra).exists():
                    sh(["git", "add", "-A", extra], check=False)
        if sh(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0:
            sh(["git", "commit", "-q", "-m", f"{self.tag} queue: {self.line or 'update'}"], check=False)
        for attempt in range(5):
            r = sh(["git", "pull", "-q", "--rebase", "--autostash"], check=False)
            if r.returncode != 0:
                sh(["git", "rebase", "--abort"], check=False)
                time.sleep(10 * 2 ** attempt)
                continue
            if sh(["git", "push", "-q"], check=False).returncode == 0:
                self.last_push = now_et()
                return True
            time.sleep(10 * 2 ** attempt)
        return False

    def git_pull(self):
        sh(["git", "pull", "-q", "--rebase", "--autostash"], check=False)

    # ---------------------------------------------------------------- status
    def status_block(self, done="", blocked="none", nxt="", needs="none"):
        with open(STATUS, "a") as fh:
            fh.write(f"\n## {stamp()}  {self.tag}\ndone: {done}\nblocked: {blocked}\nnext: {nxt}\nneeds-other-side: {needs}\n")

    def heartbeat(self, stage, progress, force=False):
        if not force and time.time() - self.last_heartbeat < 1800:
            return
        self.last_heartbeat = time.time()
        (DATA / f"heartbeat_{self.laptop}.txt").write_text(
            f"{now_et().isoformat(timespec='seconds')}\nstage: {stage}\nprogress: {progress}\n"
            f"max_seeds: {self.max_seeds}\nrungs: {self.rungs}\n")
        self.git_sync(light=True)

    def tick(self, text):
        lp = self.last_push.strftime("%H:%M") if self.last_push else "never"
        self.line = text
        print(f"{stamp()} · {text} · last push {lp}", flush=True)

    # ---------------------------------------------------------------- running a stage
    def run_stage(self, name, argv, after):
        t0 = time.time()
        log = ROOT / "logs" / f"{self.laptop}_{name}.log"
        log.parent.mkdir(exist_ok=True)
        progress = "starting"
        with open(log, "a") as lf:
            p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            last_tick = 0.0
            for line in p.stdout:
                lf.write(line)
                lf.flush()
                if line.startswith("#progress"):
                    parts = dict(x.split("=") for x in line.split()[3:] if "=" in x)
                    pct = line.split()[2]
                    eta = int(float(parts.get("eta_s", -1)))
                    progress = f"{pct}% · ETA {eta // 3600:02d}:{(eta % 3600) // 60:02d}" if eta >= 0 else f"{pct}%"
                if time.time() - last_tick >= 60:
                    last_tick = time.time()
                    self.tick(f"{name} · {progress}")
                    self.heartbeat(name, progress)
            p.wait()
        if p.returncode != 0:
            tail = "".join(open(log).readlines()[-30:])
            raise RuntimeError(f"{name} exited {p.returncode}\n{tail}")
        if after:
            after()
        if "--out" in argv:
            self.gzip_file(ROOT / argv[argv.index("--out") + 1])
        secs = time.time() - t0
        if name.startswith("Q2_seed"):
            self.pass_durations.append(secs)
            self.ladder(secs)
        self.marker(name).write_text(f"{stamp()} {secs:.0f}s\n")
        self.status_block(done=f"{name} finished in {secs / 60:.0f} min (ladder: max_seeds={self.max_seeds}, rungs={self.rungs or 'none'})",
                          nxt="next runnable stage")
        self.tick(f"{name} done in {secs / 60:.0f} min")
        self.git_sync()

    def ladder(self, secs):
        remaining = self.max_seeds - len(self.pass_durations)
        finish = now_et() + dt.timedelta(seconds=secs * remaining)
        deadline = parse_et("2026-10-11T06:00")
        if secs > PASS_BUDGET_H * 3600 and self.max_seeds > 10:
            self.max_seeds = 10
            self.rungs.append("seeds_10")
        elif finish > deadline and self.laptop == "ian" and "ghz8_5" not in self.rungs:
            self.rungs.append("ghz8_5")
        elif finish > deadline and self.laptop == "thomas" and "drop_qaoa6" not in self.rungs:
            self.rungs.append("drop_qaoa6")
        elif finish > deadline and self.max_seeds > 10:
            self.max_seeds = 10
            self.rungs.append("seeds_10")

    # ---------------------------------------------------------------- main loop
    def loop(self):
        self.status_block(done=f"queue started on {self.laptop} ({sys.platform}, python {sys.version.split()[0]})",
                          nxt="first runnable stage")
        self.git_sync()
        idle_since = None
        while now_et() < self.until:
            try:
                self.git_pull()
                runnable = next(((n, argv, after) for n, ok, argv, after in self.stages() if ok and not self.done(n)), None)
                if runnable is None:
                    if idle_since is None:
                        idle_since = time.time()
                    self.tick("idle · waiting for inputs (next pull in 5 min)")
                    self.heartbeat("idle", "waiting")
                    time.sleep(300)
                    continue
                idle_since = None
                name, argv, after = runnable
                self.tick(f"{name} · starting")
                self.run_stage(name, argv, after)
            except KeyboardInterrupt:
                raise
            except Exception:
                tb = traceback.format_exc().splitlines()[-30:]
                self.status_block(done="", blocked=f"{self.line}\n" + "\n".join(tb), nxt="retry after the next pull")
                self.tick("blocked · see STATUS.md · sleeping 5 min")
                try:
                    self.git_sync()
                except Exception:
                    pass
                time.sleep(300)
        self.status_block(done="queue finished (until reached)", nxt="nothing; freeze")
        self.git_sync()
        return 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laptop", choices=["ian", "thomas"], required=True)
    ap.add_argument("--until", default="2026-10-11T09:00")
    ap.add_argument("--also", default="", help="extra circuits for this laptop's Q2 passes (comma list)")
    ap.add_argument("--skip", default="", help="circuits to drop from this laptop's Q2 passes")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    a.also = [c for c in a.also.split(",") if c]
    a.skip = [c for c in a.skip.split(",") if c]
    q = Queue(a)
    if a.dry_run:
        for n, ok, argv, after in q.stages():
            state = "done" if q.done(n) else ("runnable" if ok else "waiting")
            print(f"{n:14s} {state:9s} {' '.join(argv[2:]) if isinstance(argv, list) else argv}")
        return 0
    return q.loop()


if __name__ == "__main__":
    sys.exit(main())
