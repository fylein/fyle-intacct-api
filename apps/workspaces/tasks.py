import time
import logging
from datetime import datetime, timedelta, date
from typing import List

from django.conf import settings
from django.db.models import Q

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting, ExpenseAttribute
from apps.fyle.models import ExpenseGroup
from apps.fyle.tasks import create_expense_groups
from apps.sage_intacct.tasks import schedule_expense_reports_creation, schedule_bills_creation, \
    schedule_charge_card_transaction_creation, schedule_journal_entries_creation
from apps.tasks.models import TaskLog
from apps.workspaces.models import LastExportDetail, Workspace, WorkspaceSchedule, Configuration, SageIntacctCredential, FyleCredential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def export_to_intacct(workspace_id, export_mode=None):
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    last_export_detail = LastExportDetail.objects.get(workspace_id=workspace_id)
    workspace_schedule = WorkspaceSchedule.objects.filter(workspace_id=workspace_id).first()

    last_exported_at = datetime.now()
    is_expenses_exported = False

    if configuration.reimbursable_expenses_object:
        expense_group_ids = ExpenseGroup.objects.filter(
            fund_source='PERSONAL', exported_at__isnull=True).values_list('id', flat=True)

        if len(expense_group_ids):
            is_expenses_exported = True

        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT':
            schedule_expense_reports_creation(
                workspace_id=workspace_id, expense_group_ids=expense_group_ids
            )

        elif configuration.reimbursable_expenses_object == 'BILL':
            schedule_bills_creation(
                workspace_id=workspace_id, expense_group_ids=expense_group_ids
            )

        elif configuration.reimbursable_expenses_object == 'JOURNAL_ENTRY':
            schedule_journal_entries_creation(
                workspace_id=workspace_id, expense_group_ids=expense_group_ids
            )

    if configuration.corporate_credit_card_expenses_object:
        expense_group_ids = ExpenseGroup.objects.filter(
            fund_source='CCC', exported_at__isnull=True).values_list('id', flat=True)

        if len(expense_group_ids):
            is_expenses_exported = True

        if configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
            schedule_charge_card_transaction_creation(
                workspace_id=workspace_id, expense_group_ids=expense_group_ids
            )

        elif configuration.corporate_credit_card_expenses_object == 'BILL':
            schedule_bills_creation(
                workspace_id=workspace_id, expense_group_ids=expense_group_ids
            )

        elif configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            schedule_expense_reports_creation(
                workspace_id=workspace_id, expense_group_ids=expense_group_ids
            )

        elif configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY':
            schedule_journal_entries_creation(
                workspace_id=workspace_id, expense_group_ids=expense_group_ids
            )

    if is_expenses_exported:
        last_export_detail.last_exported_at = last_exported_at
        last_export_detail.export_mode = export_mode or 'MANUAL'

        if workspace_schedule:
            last_export_detail.next_export_at = last_exported_at + timedelta(hours=workspace_schedule.interval_hours)

        last_export_detail.save()


def schedule_email_notification(workspace_id: int, schedule_enabled: bool, hours: int):
    if schedule_enabled:
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.workspaces.tasks.run_email_notification',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': hours * 60,
                'next_run': datetime.now() + timedelta(minutes=10)
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.workspaces.tasks.run_email_notification',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()


def schedule_sync(workspace_id: int, schedule_enabled: bool, hours: int, email_added: List, emails_selected: List):
    ws_schedule, _ = WorkspaceSchedule.objects.get_or_create(
        workspace_id=workspace_id
    )

    schedule_email_notification(workspace_id=workspace_id, schedule_enabled=schedule_enabled, hours=hours)

    if schedule_enabled:
        ws_schedule.enabled = schedule_enabled
        ws_schedule.start_datetime = datetime.now()
        ws_schedule.interval_hours = hours
        ws_schedule.emails_selected = emails_selected
        
        if email_added:
            ws_schedule.additional_email_options.append(email_added)


        schedule, _ = Schedule.objects.update_or_create(
            func='apps.workspaces.tasks.run_sync_schedule',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': hours * 60,
                'next_run': datetime.now()
            }
        )

        ws_schedule.schedule = schedule

        ws_schedule.save()

    elif not schedule_enabled and ws_schedule.schedule:
        schedule = ws_schedule.schedule
        ws_schedule.enabled = schedule_enabled
        ws_schedule.schedule = None
        ws_schedule.save()
        schedule.delete()

    return ws_schedule


def run_sync_schedule(workspace_id):
    """
    Run schedule
    :param workspace_id: workspace id
    :return: None
    """
    task_log, _ = TaskLog.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    configuration = Configuration.objects.get(workspace_id=workspace_id)

    fund_source = []
    if configuration.corporate_credit_card_expenses_object:
        fund_source.append('CCC')
    if configuration.reimbursable_expenses_object:
        fund_source.append('PERSONAL')


    create_expense_groups(
        workspace_id=workspace_id, fund_source=fund_source, task_log=task_log
    )

    if task_log.status == 'COMPLETE':
        export_to_intacct(workspace_id, 'AUTO')


def run_email_notification(workspace_id):

    ws_schedule, _ = WorkspaceSchedule.objects.get_or_create(
        workspace_id=workspace_id
    )

    task_logs = TaskLog.objects.filter(
        ~Q(type__in=['CREATING_REIMBURSEMENT', 'FETCHING_EXPENSES', 'CREATING_AP_PAYMENT']),
        workspace_id=workspace_id,
        status='FAILED'
    )

    workspace = Workspace.objects.get(id=workspace_id)
    admin_data = WorkspaceSchedule.objects.get(workspace_id=workspace_id)
    try:
        intacct = SageIntacctCredential.objects.get(workspace=workspace)
    except SageIntacctCredential.DoesNotExist:
        logger.info('SageIntacct Credentials does not exist - %s', workspace_id)
        return

    if ws_schedule.enabled:
        for admin_email in admin_data.emails_selected:
            attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, value=admin_email).first()
            
            admin_name = 'Admin'
            if attribute:
                admin_name = attribute.detail['full_name']
            else:
                for data in admin_data.additional_email_options:
                    if data['email'] == admin_email:
                        admin_name = data['name']

            if workspace.last_synced_at and workspace.ccc_last_synced_at:
                export_time = max(workspace.last_synced_at, workspace.ccc_last_synced_at)
            else:
                export_time =  workspace.last_synced_at or workspace.ccc_last_synced_at

            if task_logs and (ws_schedule.error_count is None or len(task_logs) > ws_schedule.error_count):
                context = {
                    'name': admin_name,
                    'errors': len(task_logs),
                    'fyle_company': workspace.name,
                    'intacct_company': intacct.si_company_name,
                    'workspace_id': workspace_id,
                    'export_time': export_time.date() if export_time else datetime.now(),
                    'year': date.today().year,
                    'app_url': "{0}/workspaces/{1}/expense_groups".format(settings.FYLE_APP_URL, workspace_id)
                    }
                message = render_to_string("mail_template.html", context)

                mail = EmailMessage(
                    subject="Export To Sage Intacct Failed",
                    body=message,
                    from_email=settings.EMAIL,
                    to=[admin_email],
                )

                mail.content_subtype = "html"
                mail.send()

        ws_schedule.error_count = len(task_logs)
        ws_schedule.save()

def async_update_fyle_credentials(fyle_org_id: str, refresh_token: str):
    fyle_credentials = FyleCredential.objects.filter(workspace__fyle_org_id=fyle_org_id).first()
    if fyle_credentials:
        fyle_credentials.refresh_token = refresh_token
        fyle_credentials.save()
