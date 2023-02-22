-- Script to set exported_at to updated_at of bills / charge_card_transactions and expense_reports for existing expense groups
rollback;
begin;

-- expense_reports
update expense_groups
set exported_at = expense_reports.updated_at
from expense_reports 
where expense_reports.expense_group_id = expense_groups.id;

-- charge_card_transactions
update expense_groups
set exported_at = charge_card_transactions.updated_at
from charge_card_transactions 
where charge_card_transactions.expense_group_id = expense_groups.id;

-- bills
update expense_groups
set exported_at = bills.updated_at
from bills 
where bills.expense_group_id = expense_groups.id;