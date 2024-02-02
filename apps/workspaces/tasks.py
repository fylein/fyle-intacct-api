import logging
from datetime import datetime, timedelta, date
from typing import List
import json

from django.conf import settings
from django.db.models import Q

from django.core.mail import EmailMessage
from apps.fyle.helpers import post_request
from django.template.loader import render_to_string
from django_q.models import Schedule

from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from fyle_rest_auth.helpers import get_fyle_admin

from apps.fyle.tasks import create_expense_groups
from .actions import export_to_intacct

from apps.tasks.models import TaskLog

from apps.workspaces.models import (
    Workspace,
    WorkspaceSchedule,
    Configuration,
    SageIntacctCredential,
    FyleCredential
)


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def schedule_email_notification(workspace_id: int, schedule_enabled: bool):
    if schedule_enabled:
        schedule, _ = Schedule.objects.update_or_create(
            func='apps.workspaces.tasks.run_email_notification',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
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

    schedule_email_notification(workspace_id=workspace_id, schedule_enabled=schedule_enabled)

    if schedule_enabled:
        ws_schedule.enabled = schedule_enabled
        ws_schedule.start_datetime = datetime.now()
        ws_schedule.interval_hours = hours
        ws_schedule.emails_selected = emails_selected
        
        if email_added:
            ws_schedule.additional_email_options = email_added

        # create next run by adding hours to current time
        next_run = datetime.now() + timedelta(hours=hours)

        schedule, _ = Schedule.objects.update_or_create(
            func='apps.workspaces.tasks.run_sync_schedule',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': hours * 60,
                'next_run': next_run
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
            attribute = ExpenseAttribute.objects.filter(workspace_id=workspace_id, value=admin_email, attribute_type='EMPLOYEE').first()
            
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
                    'app_url': "{0}/app/settings/#/integrations/native_apps?integrationIframeTarget=integrations/intacct".format(settings.FYLE_APP_URL)
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


def post_to_integration_settings(workspace_id: int, active: bool):
    """
    Post to integration settings
    """
    refresh_token = FyleCredential.objects.get(workspace_id=workspace_id).refresh_token
    url = '{}/integrations/'.format(settings.INTEGRATIONS_SETTINGS_API)
    payload = {
        'tpa_id': settings.FYLE_CLIENT_ID,
        'tpa_name': 'Fyle Sage Intacct Integration',
        'type': 'ACCOUNTING',
        'is_active': active,
        'connected_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    }

    try:
        post_request(url, json.dumps(payload), refresh_token)
    except Exception as error:
        logger.error(error)


def async_create_admin_subcriptions(workspace_id: int) -> None:
    """
    Create admin subscriptions
    :param workspace_id: workspace id
    :return: None
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)
    payload = {
        'is_enabled': True,
        'webhook_url': '{}/workspaces/{}/fyle/exports/'.format(settings.API_URL, workspace_id)
    }
    platform.subscriptions.post(payload)


def async_update_workspace_name(workspace: Workspace, access_token: str):
    fyle_user = get_fyle_admin(access_token.split(' ')[1], None)
    org_name = fyle_user['data']['org']['name']

    workspace.name = org_name
    workspace.save()
