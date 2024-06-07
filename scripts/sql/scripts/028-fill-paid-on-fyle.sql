rollback;
begin;

UPDATE expenses e
SET paid_on_fyle = 't'
FROM reimbursements r
WHERE e.settlement_id = r.settlement_id 
  AND e.paid_on_sage_intacct = 't' 
  AND r.state = 'COMPLETE';
