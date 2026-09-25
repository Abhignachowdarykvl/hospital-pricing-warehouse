# Hospital Pricing & Quality Warehouse

End-to-end data pipeline demonstrating data engineering and analytics skills across the full modern data stack.

## Business Problem

Hospital pricing in the US is opaque: the same procedure can cost 10× more at one hospital than another in the same city. This project builds a warehouse that makes CMS public pricing and quality data queryable, so a payer, employer, or patient advocate can answer:

- Which procedures have the widest price variation nationally?
- Do higher-rated hospitals charge more?
- Which hospitals are outliers (charging 3× their state average)?

## Architecture

```
CMS Medicare API ──► Python ingest ──► data/raw/ (JSON pages)
                                    ──► S3 (raw zone backup)
                                    ──► PostgreSQL raw schema
                                    ──► dbt (staging → marts)
                                    ──► Tableau dashboard
                         Airflow orchestrates the full pipeline monthly
                         GitHub Actions runs tests on every push
```

## Data Sources

| Dataset | Source | Rows |
|---|---|---|
| Medicare Inpatient Charges by Provider & DRG | data.cms.gov | ~145,000 |
| Hospital General Information (star ratings) | data.cms.gov/provider-data | ~5,000 |

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow |
| Ingestion | Python (requests, pydantic-settings) |
| Cloud storage | AWS S3 |
| Database | PostgreSQL 16 (Docker) |
| Transformation | dbt Core + dbt_utils |
| Testing | dbt tests, pytest, GitHub Actions CI |
| Visualization | Tableau Public |

## Data Model

```
fact_procedure_charges  (provider_ccn, drg_code, charges, payments)
    ├── dim_hospital    (provider_ccn, name, state, rating_tier)
    └── dim_drg         (drg_code, description)
         └── rpt_charge_variation  (state-level aggregation for dashboard)
```

## Quick Start

```bash
# 1. Clone and set up environment
git clone https://github.com/Abhignachowdarykvl/hospital-pricing-warehouse.git
cd hospital-pricing-warehouse
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your values

# 2. Start database
docker compose up -d

# 3. Run the pipeline
python -m src.ingest.cms_api --dataset inpatient
python -m src.ingest.cms_api --dataset hospital_info
python -m src.load.postgres_loader --dataset inpatient
python -m src.load.postgres_loader --dataset hospital_info

# 4. Run dbt
cd dbt && dbt deps && dbt run && dbt test

# 5. Run analysis queries
docker exec -i hpw_postgres psql -U hpw -d hospital_pricing < sql/02_analysis_queries.sql
```

## Key Findings

> Dashboard: [Hospital Pricing & Quality Analysis](https://public.tableau.com/app/profile/abhigna.chowdary/viz/HospitalPricingQualityAnalysis/HospitalPricingQualityAnalysis)

- CAR T-Cell Immunotherapy has the widest national charge spread at $6.8M between cheapest and most expensive hospital
- High-rated hospitals charge the most on average ($101,449) but low-rated hospitals charge more than average-rated ($96,510 vs $88,791) — quality rating is a weak predictor of cost
- California is the most expensive state ($199,960 avg charge), followed by Colorado ($198,786) and Nevada ($187,625)
- Several hospitals charge 4–5× their state average for the same procedure

## Project Structure

```
hospital-pricing-warehouse/
├── src/
│   ├── common/         # config, logging
│   ├── ingest/         # CMS API + S3 upload
│   └── load/           # Postgres loader
├── dbt/
│   ├── models/
│   │   ├── staging/    # type casting, renaming
│   │   └── marts/      # dim_hospital, dim_drg, fact_procedure_charges, rpt_charge_variation
│   └── packages.yml
├── airflow/dags/       # monthly orchestration DAG
├── sql/                # ad-hoc analysis queries
├── tests/              # pytest unit tests
├── .github/workflows/  # CI (lint + test on every push)
├── docker-compose.yml
└── requirements.txt
```

## Skills Demonstrated

`API ingestion` `pagination & retries` `AWS S3` `PostgreSQL` `dbt` `dimensional modeling`
`star schema` `data quality tests` `pytest` `CI/CD` `Docker` `Airflow` `SQL window functions`
`Tableau` `business insight`

## Interview Questions This Project Answers

- How does your pipeline handle API failures mid-run?
- Why did you keep raw data as TEXT and cast in dbt?
- How do you make a re-run safe (idempotency)?
- What does SCD Type 2 mean and where would you add it here?
- How do you know the load count matches the extract count?
- What would break if CMS added a new column?
