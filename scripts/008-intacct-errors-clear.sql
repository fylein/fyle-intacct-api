rollback;
begin;

update task_logs set sage_intacct_errors = null where status = 'COMPLETE' and sage_intacct_errors is not null;