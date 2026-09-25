select distinct
    drg_code,
    drg_description,
    -- extract the MDC prefix (first 3 chars) to group DRGs into service lines
    left(drg_description, strpos(drg_description, ' ') - 1) as drg_prefix
from {{ ref('stg_cms_inpatient_charges') }}
