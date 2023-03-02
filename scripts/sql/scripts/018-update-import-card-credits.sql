rollback;
begin;

UPDATE expense_group_settings
SET import_card_credits = 't'
WHERE workspace_id in (
    SELECT workspace_id 
    from configurations 
    where corporate_credit_card_expenses_object IN ('EXPENSE_REPORT', 'BILL', 'JOURNAL_ENTRY')
);
