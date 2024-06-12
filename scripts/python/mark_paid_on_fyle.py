from apps.fyle.models import Expense, Reimbursement
from apps.workspaces.models import Configuration

workspace_ids = Configuration.objects.filter(sync_sage_intacct_to_fyle_payments=True).values_list('workspace_id', flat=True)
count = 0
for workspace_id in workspace_ids:
    expenses = Expense.objects.filter(workspace_id=workspace_id, paid_on_sage_intacct=True)
    for expense in expenses:
        reimbursement = Reimbursement.objects.get(settlement_id=expense.settlement_id)
        if reimbursement.state == 'COMPLETE' and expense.paid_on_fyle is False:
            expense.paid_on_fyle = True
            expense.save()
            count += 1

print("Number of expenses updated", count)

