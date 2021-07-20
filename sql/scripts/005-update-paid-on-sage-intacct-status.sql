-- Script to set paid_on_sage_intacct and payment_synced as True for existing bills, expense reports and expenses
rollback;
begin;

-- bills
update bills
set paid_on_sage_intacct = True
where bills.paid_on_sage_intacct = False;

-- expense reports
update expense_reports
set paid_on_sage_intacct = True
where expense_reports.paid_on_sage_intacct = False;

-- expenses
update expenses
set paid_on_sage_intacct = True
where expenses.paid_on_sage_intacct = False;

-- payment_synced status for bills
update bills
set payment_synced = True
where bills.payment_synced = False;

-- payment_synced status for bills
update expense_reports
set payment_synced = True
where expense_reports.payment_synced = False;