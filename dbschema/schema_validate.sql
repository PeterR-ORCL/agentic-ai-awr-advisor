spool schema_validate.log
set echo on
set timing on
set serveroutput on

select table_name
from user_tables
where table_name like 'AWR_%'
order by table_name;

select view_name
from user_views
order by view_name;

select index_name, table_name, status
from user_indexes
where table_name like 'AWR_%'
order by table_name, index_name;

select model_code, model_version, status
from awr_scoring_model;

select feature_code, weight_value
from awr_scoring_weight
order by feature_code;

spool off
