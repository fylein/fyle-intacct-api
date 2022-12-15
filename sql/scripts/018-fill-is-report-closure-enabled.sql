rollback;
begin;

update 
  configurations
set 
  is_simplify_report_closure_enabled = false;
