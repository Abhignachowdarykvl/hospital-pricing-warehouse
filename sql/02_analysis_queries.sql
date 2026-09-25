-- ── Analysis 1: Top 10 DRGs with the widest national charge spread ──────────
-- Business insight: these are the procedures where shopping around matters most.
SELECT
    drg_code,
    drg_description,
    SUM(total_discharges)               AS national_volume,
    ROUND(AVG(avg_charge), 0)           AS national_avg_charge,
    ROUND(MAX(max_charge)
          - MIN(min_charge), 0)         AS max_spread_usd
FROM public_marts.rpt_charge_variation
GROUP BY 1, 2
ORDER BY max_spread_usd DESC
LIMIT 10;

-- ── Analysis 2: Do higher-rated hospitals charge more? ──────────────────────
-- Business insight: quality vs cost tradeoff.
SELECT
    rating_tier,
    COUNT(DISTINCT provider_ccn)        AS hospitals,
    ROUND(AVG(avg_submitted_charge), 0) AS avg_charge,
    ROUND(AVG(avg_medicare_payment), 0) AS avg_medicare_payment,
    ROUND(AVG(medicare_pct_of_charge), 1) AS avg_medicare_pct
FROM public_marts.fact_procedure_charges f
JOIN public_marts.dim_hospital h USING (provider_ccn)
GROUP BY 1
ORDER BY avg_charge DESC;

-- ── Analysis 3: Most expensive states (avg charge across all DRGs) ──────────
SELECT
    state,
    COUNT(DISTINCT provider_ccn)        AS hospitals,
    ROUND(AVG(avg_charge), 0)           AS avg_charge,
    ROUND(AVG(avg_medicare_pct), 1)     AS avg_medicare_pct
FROM public_marts.rpt_charge_variation
GROUP BY 1
ORDER BY avg_charge DESC
LIMIT 15;

-- ── Analysis 4: Outlier hospitals (charge > 3x state average for same DRG) ──
WITH state_avg AS (
    SELECT drg_code, state,
           AVG(avg_submitted_charge) AS state_avg_charge
    FROM public_marts.fact_procedure_charges f
    JOIN public_marts.dim_hospital h USING (provider_ccn)
    GROUP BY 1, 2
)
SELECT
    h.hospital_name,
    h.city,
    h.state,
    h.overall_rating,
    f.drg_code,
    d.drg_description,
    f.avg_submitted_charge,
    ROUND(s.state_avg_charge, 0)        AS state_avg,
    ROUND(f.avg_submitted_charge
          / NULLIF(s.state_avg_charge, 0), 2) AS ratio_to_state_avg
FROM public_marts.fact_procedure_charges f
JOIN public_marts.dim_hospital h   USING (provider_ccn)
JOIN public_marts.dim_drg d        USING (drg_code)
JOIN state_avg s            USING (drg_code, state)
WHERE f.avg_submitted_charge > 3 * s.state_avg_charge
ORDER BY ratio_to_state_avg DESC
LIMIT 20;
