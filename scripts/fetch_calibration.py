"""Fetch the ibm_fez calibration dataset and derive the daily table.

  python scripts/fetch_calibration.py --download   # raw parquet -> data/raw/ (gitignored)
  python scripts/fetch_calibration.py --derive     # raw -> data/calibration_daily_fez.parquet (committed)

The revision hash is pinned in automitigate.noise_model.HF_REVISION. The CC-BY-NC
`SN` column of the dataset is never read (load_calibration selects columns).
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automitigate.noise_model import (DAILY_PATH, HF_REPO, HF_REVISION, RAW_PATH,  # noqa: E402
                                      derive_daily, load_calibration, save_daily, snapshots)


def download():
    from huggingface_hub import hf_hub_download, list_repo_files
    files = [f for f in list_repo_files(HF_REPO, repo_type="dataset", revision=HF_REVISION)
             if f.endswith(".parquet")]
    if len(files) != 1:
        raise SystemExit(f"expected one parquet file in {HF_REPO}, found {files}")
    local = hf_hub_download(HF_REPO, files[0], repo_type="dataset", revision=HF_REVISION)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(local, RAW_PATH)
    print(f"saved {RAW_PATH} ({RAW_PATH.stat().st_size / 1e6:.1f} MB) from {HF_REPO}@{HF_REVISION[:8]}")


def derive():
    if not RAW_PATH.exists():
        raise SystemExit(f"{RAW_PATH} missing; run --download first")
    df = load_calibration(RAW_PATH)
    daily = derive_daily(df)
    save_daily(daily, DAILY_PATH)
    days = snapshots(daily)
    print(f"saved {DAILY_PATH} ({DAILY_PATH.stat().st_size / 1e6:.1f} MB): {len(daily)} rows, "
          f"{len(days)} days {days[0]} -> {days[-1]}, {len(daily.attrs['recal_days'])} recalibration days")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--derive", action="store_true")
    a = ap.parse_args()
    if not (a.download or a.derive):
        ap.error("pass --download and/or --derive")
    if a.download:
        download()
    if a.derive:
        derive()
