-- Script to set paid_on_sage_intacct as True for existing bills, expense reports and expenses
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