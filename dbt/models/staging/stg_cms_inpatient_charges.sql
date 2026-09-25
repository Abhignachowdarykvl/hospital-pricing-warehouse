-- Cast every raw TEXT column to its correct type and rename to snake_case.
-- This is the only place types change; marts build on typed columns.
with source as (
    select * from {{ source('raw', 'cms_inpatient_charges') }}
),
renamed as (
    select
        rndrng_prvdr_ccn                        as provider_ccn,
        rndrng_prvdr_org_name                   as provider_name,
        rndrng_prvdr_city                       as provider_city,
        rndrng_prvdr_st                         as provider_street,
        rndrng_prvdr_state_abrvtn               as provider_state,
        rndrng_prvdr_state_fips                 as provider_state_fips,
        rndrng_prvdr_zip5                       as provider_zip,
        rndrng_prvdr_ruca                       as ruca_code,
        rndrng_prvdr_ruca_desc                  as ruca_description,
        drg_cd                                  as drg_code,
        drg_desc                                as drg_description,
        tot_dschrgs::integer                    as total_discharges,
        avg_submtd_cvrd_chrg::numeric(12,2)     as avg_submitted_charge,
        avg_tot_pymt_amt::numeric(12,2)         as avg_total_payment,
        avg_mdcr_pymt_amt::numeric(12,2)        as avg_medicare_payment,
        _run_date::date                         as run_date
    from source
)
select * from renamed
