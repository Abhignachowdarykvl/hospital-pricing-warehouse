# Hospital Pricing & Quality Warehouse

End-to-end data pipeline: CMS Medicare API → S3 → PostgreSQL → dbt → Tableau, orchestrated with Airflow.

**Status:** work in progress. Full README, architecture diagram, and dashboard link coming as the project completes.

## Quick start
```bash
cp .env.example .env          # fill in values
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d
python -m src.ingest.cms_api --dataset inpatient
```
