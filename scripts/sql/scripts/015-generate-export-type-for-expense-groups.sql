-- Script to add export_type to expense_groups table based on task_logs

rollback;
begin;

update expense_groups set export_type = 'EXPENSE_REPORT' where id in (
        select expense_group_id from task_logs where type = 'CREATING_EXPENSE_REPORTS' and status = 'COMPLETE' and expense_report_id is not null
    );

update expense_groups set export_type = 'BILL' where id in (
        select expense_group_id from task_logs where type = 'CREATING_BILLS' and status = 'COMPLETE' and bill_id is not null
    );

update expense_groups set export_type = 'JOURNAL_ENTRY' where id in (
        select expense_group_id from task_logs where type = 'CREATING_JOURNAL_ENTRIES' and status = 'COMPLETE' and journal_entry_id is not null
    );

update expense_groups set export_type = 'CHARGE_CARD_TRANSACTION' where id in (
        select expense_group_id from task_logs where type = 'CREATING_CHARGE_CARD_TRANSACTIONS' and status = 'COMPLETE' and charge_card_transaction_id is not null
    );


