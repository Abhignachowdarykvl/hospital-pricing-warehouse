-- Central fact table: one row per hospital + DRG combination.
-- All monetary values are in USD. Totals are estimated (avg * discharges).
select
    {{ dbt_utils.generate_surrogate_key(['provider_ccn', 'drg_code']) }} as charge_id,
    provider_ccn,
    drg_code,
    run_date,
    total_discharges,
    avg_submitted_charge,
    avg_total_payment,
    avg_medicare_payment,
    -- estimated revenue for this DRG at this hospital
    round(avg_total_payment * total_discharges, 2)      as est_total_revenue,
    -- gap between what was billed and what Medicare paid
    round(avg_submitted_charge - avg_medicare_payment, 2) as charge_to_payment_gap,
    -- Medicare payment as a % of submitted charge
    round(
        avg_medicare_payment / nullif(avg_submitted_charge, 0) * 100, 2
    )                                                   as medicare_pct_of_charge
from {{ ref('stg_cms_inpatient_charges') }}
