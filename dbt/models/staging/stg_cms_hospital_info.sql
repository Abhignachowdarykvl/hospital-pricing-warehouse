with source as (
    select * from {{ source('raw', 'cms_hospital_info') }}
),
renamed as (
    select
        facility_id as provider_ccn,
        facility_name as hospital_name,
        address as street_address,
        citytown as city,
        state,
        zip_code as zip,
        countyparish as county,
        telephone_number as phone,
        hospital_type,
        hospital_ownership as ownership,
        emergency_services,
        nullif(hospital_overall_rating, 'Not Available')::integer as overall_rating,
        nullif(hospital_overall_rating_footnote, 'Not Available') as rating_footnote,
        _run_date::date as run_date,
        row_number() over (
            partition by facility_id
            order by _run_date desc
        ) as rn
    from source
)
select
    provider_ccn, hospital_name, street_address, city, state,
    zip, county, phone, hospital_type, ownership, emergency_services,
    overall_rating, rating_footnote, run_date
from renamed
where rn = 1
