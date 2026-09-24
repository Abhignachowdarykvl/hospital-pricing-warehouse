"""Ingest CMS datasets into a local raw zone as JSON pages.

Design goals (these are the things to talk about in an interview):
- Pagination: CMS APIs return at most a few thousand rows per call, so we
  walk offset/size pages until a page comes back short.
- Resilience: a requests.Session with automatic retries and backoff handles
  transient 429/5xx errors without crashing the run.
- Idempotency: every run writes to data/raw/<dataset>/<run_date>/, so
  re-running the same day overwrites cleanly and different days never collide.
- Raw means raw: we store the API response untouched. Cleaning happens later
  (dbt), which keeps the ingestion step simple and auditable.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.common.config import settings
from src.common.logging import get_logger

log = get_logger(__name__)

RAW_DIR = Path("data/raw")

# Two CMS API families. Both use offset pagination but have different URL shapes.
DATASETS = {
    # data.cms.gov "data-api": Medicare Inpatient Hospitals - by Provider and Service
    "inpatient": {
        "url": "https://data.cms.gov/data-api/v1/dataset/{id}/data",
        "id": settings.cms_inpatient_dataset_id,
        "page_size": 5000,
    },
    # data.cms.gov/provider-data datastore: Hospital General Information
    "hospital_info": {
        "url": "https://data.cms.gov/provider-data/api/1/datastore/query/{id}/0",
        "id": settings.cms_hospital_info_dataset_id,
        "page_size": 500,
    },
}


def build_session(retries: int = 5, backoff: float = 1.0) -> requests.Session:
    """HTTP session that retries on rate limits and server errors."""
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "hospital-pricing-warehouse/0.1"})
    return session


def fetch_page(session: requests.Session, url: str, offset: int, size: int) -> list[dict]:
    resp = session.get(url, params={"offset": offset, "size": size}, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    # The provider-data datastore wraps rows in {"results": [...]}; data-api returns a list.
    if isinstance(payload, dict):
        return payload.get("results", [])
    return payload


def ingest(dataset: str, max_pages: int | None = None) -> Path:
    cfg = DATASETS[dataset]
    if not cfg["id"]:
        raise ValueError(f"Dataset id for '{dataset}' is empty. Set it in .env.")

    url = cfg["url"].format(id=cfg["id"])
    size = cfg["page_size"]
    run_date = datetime.now(UTC).strftime("%Y-%m-%d")
    out_dir = RAW_DIR / dataset / run_date
    out_dir.mkdir(parents=True, exist_ok=True)

    session = build_session()
    offset, page, total_rows = 0, 0, 0
    while True:
        rows = fetch_page(session, url, offset, size)
        if not rows:
            break
        (out_dir / f"page_{page:04d}.json").write_text(json.dumps(rows))
        total_rows += len(rows)
        log.info("dataset=%s page=%d rows=%d total=%d", dataset, page, len(rows), total_rows)
        page += 1
        offset += size
        if len(rows) < size or (max_pages and page >= max_pages):
            break

    manifest = {
        "dataset": dataset,
        "run_date": run_date,
        "source_url": url,
        "pages": page,
        "rows": total_rows,
        "ingested_at": datetime.now(UTC).isoformat(),
    }
    (out_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2))
    log.info("finished dataset=%s rows=%d dir=%s", dataset, total_rows, out_dir)
    return out_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a CMS dataset to the raw zone.")
    parser.add_argument("--dataset", choices=DATASETS.keys(), required=True)
    parser.add_argument("--max-pages", type=int, default=None, help="For quick test runs.")
    args = parser.parse_args()
    ingest(args.dataset, args.max_pages)
