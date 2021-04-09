rollback;
begin;

update expense_group_settings 
set corporate_credit_card_expense_group_fields = corporate_credit_card_expense_group_fields || '{"expense_id"}' 
where workspace_id in (
    select workspace_id from workspace_general_settings where 
    corporate_credit_card_expenses_object = 'CHARGE_CARD_TRANSACTION'
)
;