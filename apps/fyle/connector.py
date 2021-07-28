from typing import List
import json
import logging
import requests

from django.conf import settings

from fylesdk import FyleSDK, UnauthorizedClientError, NotFoundClientError, InternalServerError, WrongParamsError

from fyle_accounting_mappings.models import ExpenseAttribute
from apps.fyle.models import Reimbursement

logger = logging.getLogger(__name__)

class FyleConnector:
    """
    Fyle utility functions
    """

    def __init__(self, refresh_token, workspace_id=None):
        client_id = settings.FYLE_CLIENT_ID
        client_secret = settings.FYLE_CLIENT_SECRET
        base_url = settings.FYLE_BASE_URL
        self.workspace_id = workspace_id

        self.connection = FyleSDK(
            base_url=base_url,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token
        )

    def _post_request(self, url, body):
        """
        Create a HTTP post request.
        """

        access_token = self.connection.access_token
        api_headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer {0}'.format(access_token)
        }

        response = requests.post(
            url,
            headers=api_headers,
            data=body
        )

        if response.status_code == 200:
            return json.loads(response.text)

        elif response.status_code == 401:
            raise UnauthorizedClientError('Wrong client secret or/and refresh token', response.text)

        elif response.status_code == 404:
            raise NotFoundClientError('Client ID doesn\'t exist', response.text)

        elif response.status_code == 400:
            raise WrongParamsError('Some of the parameters were wrong', response.text)

        elif response.status_code == 500:
            raise InternalServerError('Internal server error', response.text)
    
    def __format_updated_at(self, updated_at):
        return 'gte:{0}'.format(datetime.strftime(updated_at, '%Y-%m-%dT%H:%M:%S.000Z'))

    def __get_last_synced_at(self, attribute_type: str):
        latest_synced_record = ExpenseAttribute.objects.filter(
            workspace_id=self.workspace_id,
            attribute_type=attribute_type
        ).order_by('-updated_at').first()
        updated_at = self.__format_updated_at(latest_synced_record.updated_at) if latest_synced_record else None

        return updated_at

    def existing_db_count(self, attribute_type: str):
        return ExpenseAttribute.objects.filter(
            workspace_id=self.workspace_id,
            attribute_type=attribute_type
        ).count()

    def _get_request(self, url, params):
        """
        Create a HTTP get request.
        """

        access_token = self.connection.access_token
        api_headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer {0}'.format(access_token)
        }
        api_params = {}

        for k in params:
            # ignore all unused params
            if not params[k] is None:
                p = params[k]

                # convert boolean to lowercase string
                if isinstance(p, bool):
                    p = str(p).lower()

                api_params[k] = p

        response = requests.get(
            url,
            headers=api_headers,
            params=api_params
        )

        if response.status_code == 200:
            return json.loads(response.text)

        elif response.status_code == 401:
            raise UnauthorizedClientError('Wrong client secret or/and refresh token', response.text)

        elif response.status_code == 404:
            raise NotFoundClientError('Client ID doesn\'t exist', response.text)

        elif response.status_code == 400:
            raise WrongParamsError('Some of the parameters were wrong', response.text)

        elif response.status_code == 500:
            raise InternalServerError('Internal server error', response.text)

    def get_employee_profile(self):
        """
        Get expenses from fyle
        """
        employee_profile = self.connection.Employees.get_my_profile()

        return employee_profile['data']

    def get_cluster_domain(self):
        """
        Get cluster domain name from fyle
        """

        body = {}
        api_url = '{0}/oauth/cluster/'.format(settings.FYLE_BASE_URL)

        return self._post_request(api_url, body)

    def get_fyle_orgs(self, cluser_domain):
        """
        Get fyle orgs of a user
        """

        params = {}
        api_url = '{0}/api/orgs/'.format(cluser_domain)

        return self._get_request(api_url, params)

    def get_expenses(self, state: List[str], fund_source: List[str], updated_at: List[str]):
        """
        Get expenses from fyle
        """
        expenses = self.connection.Expenses.get_all(state=state, fund_source=fund_source, updated_at=updated_at)
        expenses = list(filter(lambda expense: expense['amount'] > 0, expenses))
        expenses = list(
            filter(lambda expense: not (not expense['reimbursable'] and expense['fund_source'] == 'PERSONAL'),
                   expenses))

        return expenses

    def sync_employees(self):
        """
        Get employees from fyle
        """
        updated_at = self.__get_last_synced_at('EMPLOYEE')
        employees = self.connection.Employees.get_all(updated_at=updated_at)

        employee_attributes = []

        for employee in employees:
            employee_attributes.append({
                'attribute_type': 'EMPLOYEE',
                'display_name': 'Employee',
                'value': employee['employee_email'],
                'source_id': employee['id'],
                'detail': {
                    'employee_code': employee['employee_code'],
                    'full_name': employee['full_name'],
                    'location': employee['location'],
                    'department': employee['department'],
                    'department_id': employee['department_id'],
                    'department_code': employee['department_code']
                }
            })

        ExpenseAttribute.bulk_create_or_update_expense_attributes(
            employee_attributes, 'EMPLOYEE', self.workspace_id, True)

        return []

    def sync_categories(self, active_only: bool):
        """
        Get categories from fyle
        """
        existing_db_count = self.existing_db_count('CATEGORY')
        existing_category_count = self.connection.Categories.count()['count']

        if existing_db_count == existing_category_count:
            return

        categories = self.connection.Categories.get_all()

        category_attributes = []

        for category in categories:
            if category['name'] != category['sub_category']:
                category['name'] = '{0} / {1}'.format(category['name'], category['sub_category'])

            category_attributes.append({
                'attribute_type': 'CATEGORY',
                'display_name': 'Category',
                'value': category['name'],
                'source_id': category['id']
            })

        ExpenseAttribute.bulk_create_or_update_expense_attributes(
            category_attributes, 'CATEGORY', self.workspace_id)

        return []

    def sync_projects(self):
        """
        Get projects from fyle
        """
        existing_db_count = self.existing_db_count('PROJECT')
        existing_project_count = self.connection.Projects.count()['count']

        if existing_db_count == existing_project_count:
            return

        projects = self.connection.Projects.get_all()

        project_attributes = []

        for project in projects:
            project_attributes.append({
                'attribute_type': 'PROJECT',
                'display_name': 'Project',
                'value': project['name'],
                'source_id': project['id']
            })

        ExpenseAttribute.bulk_create_or_update_expense_attributes(
            project_attributes, 'PROJECT', self.workspace_id)

        return []

    def sync_cost_centers(self):
        """
        Get cost centers from fyle
        """
        existing_db_count = self.existing_db_count('COST_CENTER')
        existing_cost_centers_count = self.connection.CostCenters.count()['count']

        if existing_db_count == existing_cost_centers_count:
            return

        cost_centers = self.connection.CostCenters.get_all()

        cost_center_attributes = []

        for cost_center in cost_centers:
            cost_center_attributes.append({
                'attribute_type': 'COST_CENTER',
                'display_name': 'Cost Center',
                'value': cost_center['name'],
                'source_id': cost_center['id']
            })

        ExpenseAttribute.bulk_create_or_update_expense_attributes(
            cost_center_attributes, 'COST_CENTER', self.workspace_id)

        return []

    def sync_expense_custom_fields(self, active_only: bool = True):
        """
        Get Expense Custom Fields from Fyle (Type = Select)
        """
        expense_custom_fields = self.connection.ExpensesCustomFields.get(active=active_only)['data']

        expense_custom_fields = filter(lambda field: field['type'] == 'SELECT', expense_custom_fields)

        for custom_field in expense_custom_fields:
            expense_custom_field_attributes = []
            options = []
            count = 1

            for option in custom_field['options']:
                if option not in options:
                    expense_custom_field_attributes.append({
                        'attribute_type': custom_field['name'].upper().replace(' ', '_'),
                        'display_name': custom_field['name'],
                        'value': option,
                        'source_id': 'expense_custom_field.{}.{}'.format(custom_field['name'].lower(), count),
                        'detail': {
                            'custom_field_id': custom_field['id']
                        }
                    })
                    count = count + 1
                options.append(option)

            ExpenseAttribute.bulk_create_or_update_expense_attributes(
                expense_custom_field_attributes, custom_field['name'].upper().replace(' ', '_'),
                self.workspace_id,
                update=True
            )

        return []

    def get_attachments(self, expense_ids: List[str]):
        """
        Get attachments against expense_ids
        """
        attachments = []
        if expense_ids:
            for expense_id in expense_ids:
                attachment_file_names = []
                attachment = self.connection.Expenses.get_attachments(expense_id)
                if attachment['data']:
                    for attachment in attachment['data']:
                        if attachment['filename'] not in attachment_file_names:
                            attachment['expense_id'] = expense_id
                            attachments.append(attachment)
                            attachment_file_names.append(attachment['filename'])

            return attachments

        return []

    def sync_reimbursements(self):
        """
        Get reimbursements from fyle
        """
        latest_synced_record = Reimbursement.objects.filter(
            workspace_id=self.workspace_id
        ).order_by('-updated_at').first()
        updated_at = self.__format_updated_at(latest_synced_record.updated_at) if latest_synced_record else None

        reimbursements = self.connection.Reimbursements.get_all(updated_at=updated_at)

        Reimbursement.create_or_update_reimbursement_objects(
            reimbursements, self.workspace_id
        )

    def post_reimbursement(self, reimbursement_ids: list):
        """
        Process Reimbursements in bulk.
        """
        return self.connection.Reimbursements.post(reimbursement_ids)
