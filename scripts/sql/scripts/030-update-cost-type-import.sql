rollback;
begin;

with min_created_at as (
    select
        workspace_id,
        min(created_at) AS min_created_at
    from
        cost_types
    where
        is_imported = 'f'
    group by
        workspace_id
)
update dependent_field_settings dfs
set last_successful_import_at = (
    case 
        when dfs.last_successful_import_at >= mca.min_created_at then mca.min_created_at
        else dfs.last_successful_import_at
    end
)
from min_created_at mca
where dfs.workspace_id = mca.workspace_id
and dfs.workspace_id not in (514);