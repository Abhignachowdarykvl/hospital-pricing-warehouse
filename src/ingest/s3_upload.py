"""Upload a raw run directory to the S3 raw zone.

Layout in S3 mirrors local: s3://<bucket>/raw/<dataset>/<run_date>/<file>
Uploads are idempotent: the same key is overwritten, never duplicated.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import boto3

from src.common.config import settings
from src.common.logging import get_logger

log = get_logger(__name__)

RAW_DIR = Path("data/raw")


def latest_run_dir(dataset: str) -> Path:
    runs = sorted(p for p in (RAW_DIR / dataset).iterdir() if p.is_dir())
    if not runs:
        raise FileNotFoundError(f"No runs found under {RAW_DIR / dataset}")
    return runs[-1]


def s3_key(dataset: str, run_date: str, filename: str) -> str:
    return f"raw/{dataset}/{run_date}/{filename}"


def upload_run(dataset: str, run_dir: Path | None = None, client=None) -> int:
    if not settings.s3_bucket:
        raise ValueError("S3_BUCKET is empty. Set it in .env.")
    run_dir = run_dir or latest_run_dir(dataset)
    client = client or boto3.client("s3", region_name=settings.aws_region)

    files = sorted(run_dir.glob("*.json"))
    for f in files:
        key = s3_key(dataset, run_dir.name, f.name)
        client.upload_file(str(f), settings.s3_bucket, key)
        log.info("uploaded s3://%s/%s", settings.s3_bucket, key)
    log.info("uploaded %d files for dataset=%s run_date=%s", len(files), dataset, run_dir.name)
    return len(files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a raw run to S3.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--run-date", help="YYYY-MM-DD; defaults to the latest run.")
    args = parser.parse_args()
    run_dir = RAW_DIR / args.dataset / args.run_date if args.run_date else None
    upload_run(args.dataset, run_dir)
