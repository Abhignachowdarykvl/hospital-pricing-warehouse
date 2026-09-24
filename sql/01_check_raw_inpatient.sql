-- Sanity checks after loading raw.cms_inpatient_charges.
-- Run with: docker exec -i hpw_postgres psql -U hpw -d hospital_pricing < sql/01_check_raw_inpatient.sql

SELECT COUNT(*)                          AS total_rows,
       COUNT(DISTINCT rndrng_prvdr_ccn)  AS hospitals,
       COUNT(DISTINCT drg_cd)            AS drgs,
       MIN(_run_date), MAX(_run_date)
FROM raw.cms_inpatient_charges;

-- Any duplicate hospital + DRG combinations within a run?
SELECT rndrng_prvdr_ccn, drg_cd, _run_date, COUNT(*)
FROM raw.cms_inpatient_charges
GROUP BY 1, 2, 3
HAVING COUNT(*) > 1
LIMIT 10;
