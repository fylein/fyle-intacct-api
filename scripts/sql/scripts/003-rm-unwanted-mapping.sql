-- Script remove unwanted mapping
rollback;
begin;

delete from fyle_accounting_mappings_mappingsetting where 
source_field = 'EXPENSE_REPORT';
