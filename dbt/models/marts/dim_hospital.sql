-- One row per hospital with the latest available attributes.
-- Joining on CCN links charges to quality data.
with charges as (
    select distinct
        provider_ccn,
        provider_name,
        provider_city,
        provider_state,
        provider_zip,
        ruca_code,
        ruca_description
    from {{ ref('stg_cms_inpatient_charges') }}
),
info as (
    select
        provider_ccn,
        hospital_name,
        hospital_type,
        ownership,
        emergency_services,
        overall_rating,
        county,
        phone
    from {{ ref('stg_cms_hospital_info') }}
)
select
    c.provider_ccn,
    coalesce(i.hospital_name, c.provider_name)  as hospital_name,
    c.provider_city                              as city,
    c.provider_state                             as state,
    c.provider_zip                               as zip,
    c.ruca_code,
    c.ruca_description,
    i.hospital_type,
    i.ownership,
    i.emergency_services,
    i.overall_rating,
    i.county,
    i.phone,
    case
        when i.overall_rating >= 4 then 'High'
        when i.overall_rating = 3  then 'Average'
        when i.overall_rating <= 2 then 'Low'
        else 'Not Rated'
    end                                          as rating_tier
from charges c
left join info i using (provider_ccn)
