rollback;
begin;

update 
  'configuration' 
set 
  is_simplify_report_closure_enabled = 0;
  