rollback;
begin;

update expense_group_settings 
set corporate_credit_card_expense_group_fields = corporate_credit_card_expense_group_fields || '{"expense_id"}';