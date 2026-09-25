-- Business question: how much does the same DRG vary in price across states?
-- This is the table that feeds the Tableau dashboard.
select
    f.drg_code,
    d.drg_description,
    h.state,
    h.rating_tier,
    count(distinct f.provider_ccn)              as hospital_count,
    sum(f.total_discharges)                     as total_discharges,
    round(avg(f.avg_submitted_charge), 2)       as avg_charge,
    round(min(f.avg_submitted_charge), 2)       as min_charge,
    round(max(f.avg_submitted_charge), 2)       as max_charge,
    round(max(f.avg_submitted_charge)
          - min(f.avg_submitted_charge), 2)     as charge_range,
    round(avg(f.avg_medicare_payment), 2)       as avg_medicare_payment,
    round(avg(f.medicare_pct_of_charge), 2)     as avg_medicare_pct
from {{ ref('fact_procedure_charges') }} f
join {{ ref('dim_hospital') }} h using (provider_ccn)
join {{ ref('dim_drg') }} d using (drg_code)
group by 1, 2, 3, 4
