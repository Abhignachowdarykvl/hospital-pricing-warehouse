"""Load raw JSON pages from data/raw/<dataset>/<run_date>/ into PostgreSQL.

Why a separate raw schema:
- Every column is loaded as TEXT exactly as the API sent it. No casting, no
  renaming. If a cast fails later we can see the original value.
- Three metadata columns (_run_date, _source_file, _loaded_at) give lineage:
  for any row we can say which run and which file it came from.
- Loads are idempotent per run_date: we delete that run_date's rows first,
  then insert. Re-running never duplicates data.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.common.config import settings
from src.common.logging import get_logger

log = get_logger(__name__)

RAW_DIR = Path("data/raw")
RAW_SCHEMA = "raw"

# dataset name on disk -> table name in Postgres
TABLES = {
    "inpatient": "cms_inpatient_charges",
    "hospital_info": "cms_hospital_info",
}


def latest_run_dir(dataset: str) -> Path:
    runs = sorted(p for p in (RAW_DIR / dataset).iterdir() if p.is_dir())
    if not runs:
        raise FileNotFoundError(f"No runs found under {RAW_DIR / dataset}")
    return runs[-1]


def pages_to_frame(run_dir: Path) -> pd.DataFrame:
    """Read every page_*.json in a run directory into one DataFrame of strings."""
    frames = []
    for page in sorted(run_dir.glob("page_*.json")):
        rows = json.loads(page.read_text())
        df = pd.DataFrame(rows, dtype="string")
        df["_source_file"] = page.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No page files in {run_dir}")
    df = pd.concat(frames, ignore_index=True)
    df["_run_date"] = run_dir.name
    df["_loaded_at"] = datetime.now(UTC).isoformat()
    # Postgres prefers lowercase identifiers; keep them predictable for dbt.
    df.columns = [c.lower() for c in df.columns]
    return df


def load(dataset: str, run_dir: Path | None = None) -> int:
    table = TABLES[dataset]
    run_dir = run_dir or latest_run_dir(dataset)
    df = pages_to_frame(run_dir)
    run_date = run_dir.name

    engine = create_engine(settings.postgres_url)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}"))
        exists = conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = :s AND table_name = :t"
            ),
            {"s": RAW_SCHEMA, "t": table},
        ).scalar()
        if exists:
            deleted = conn.execute(
                text(f"DELETE FROM {RAW_SCHEMA}.{table} WHERE _run_date = :d"),
                {"d": run_date},
            ).rowcount
            log.info("removed %d existing rows for run_date=%s", deleted, run_date)

    # pandas creates the table (all TEXT) on first load, appends afterwards.
    df.to_sql(
        table,
        engine,
        schema=RAW_SCHEMA,
        if_exists="append",
        index=False,
        chunksize=10_000,
        method="multi",
    )

    with engine.begin() as conn:
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {RAW_SCHEMA}.{table} WHERE _run_date = :d"),
            {"d": run_date},
        ).scalar()

    # Reconcile against the ingestion manifest: rows extracted must equal rows loaded.
    manifest = json.loads((run_dir / "_manifest.json").read_text())
    if count != manifest["rows"]:
        raise RuntimeError(
            f"Row count mismatch: manifest={manifest['rows']} loaded={count}"
        )
    log.info("loaded %d rows into %s.%s for run_date=%s", count, RAW_SCHEMA, table, run_date)
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load a raw dataset run into Postgres.")
    parser.add_argument("--dataset", choices=TABLES.keys(), required=True)
    parser.add_argument("--run-date", help="YYYY-MM-DD; defaults to the latest run.")
    args = parser.parse_args()
    run_dir = RAW_DIR / args.dataset / args.run_date if args.run_date else None
    load(args.dataset, run_dir)
