"""
Hospital Pricing Warehouse — Monthly Pipeline DAG

Tasks (in order):
  1. ingest_inpatient   — fetch CMS inpatient charges from the API
  2. ingest_hospital    — fetch CMS hospital general information
  3. upload_s3          — upload both raw runs to S3
  4. load_postgres      — load both datasets into raw schema
  5. dbt_run            — run all dbt models
  6. dbt_test           — run all dbt tests (fails the DAG if any test fails)

Schedule: 1st of every month at 06:00 UTC (CMS refreshes monthly).
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"
PYTHON = f"{PROJECT_DIR}/.venv/bin/python"

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="hospital_pricing_warehouse",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 6 1 * *",
    catchup=False,
    tags=["cms", "healthcare", "monthly"],
) as dag:

    ingest_inpatient = BashOperator(
        task_id="ingest_inpatient",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} -m src.ingest.cms_api --dataset inpatient",
    )

    ingest_hospital = BashOperator(
        task_id="ingest_hospital_info",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} -m src.ingest.cms_api --dataset hospital_info",
    )

    upload_s3 = BashOperator(
        task_id="upload_s3",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            f"{PYTHON} -m src.ingest.s3_upload --dataset inpatient && "
            f"{PYTHON} -m src.ingest.s3_upload --dataset hospital_info"
        ),
    )

    load_postgres = BashOperator(
        task_id="load_postgres",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            f"{PYTHON} -m src.load.postgres_loader --dataset inpatient && "
            f"{PYTHON} -m src.load.postgres_loader --dataset hospital_info"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt test --profiles-dir .",
    )

    [ingest_inpatient, ingest_hospital] >> upload_s3 >> load_postgres >> dbt_run >> dbt_test
