select
    awr_id,
    dbms_lob.substr(parser_output_json, 200, 1) as parser_json_sample
from awr_report
where awr_id = 70;
