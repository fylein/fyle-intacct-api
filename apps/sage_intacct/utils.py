from typing import List, Dict
from datetime import datetime

from django.conf import settings

from fyle_accounting_mappings.models import DestinationAttribute

from sageintacctsdk import SageIntacctSDK

from apps.workspaces.models import SageIntacctCredential

from .models import ExpenseReport, ExpenseReportLineitem, Bill, BillLineitem


class SageIntacctConnector:
    """
    Sage Intacct utility functions
    """
    def __init__(self, credentials_object: SageIntacctCredential, workspace_id: int):
        sender_id = settings.SI_SENDER_ID
        sender_password = settings.SI_SENDER_PASSWORD

        self.connection = SageIntacctSDK(
            sender_id=sender_id,
            sender_password=sender_password,
            user_id=credentials_object.si_user_id,
            company_id=credentials_object.si_company_id,
            user_password=credentials_object.si_user_password
        )

        self.workspace_id = workspace_id

        credentials_object.save()

    def sync_accounts(self):
        """
        Get accounts
        """
        accounts = self.connection.accounts.get_all()

        account_attributes = []

        for account in accounts:
            account_attributes.append({
                'attribute_type': 'ACCOUNT',
                'display_name': 'account',
                'value': account['TITLE'],
                'destination_id': account['ACCOUNTNO']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            account_attributes, self.workspace_id)
        return account_attributes

    def sync_departments(self):
        """
        Get departments
        """
        departments = self.connection.departments.get_all()

        department_attributes = []

        for department in departments:
            department_attributes.append({
                'attribute_type': 'DEPARTMENT',
                'display_name': 'department',
                'value': department['TITLE'],
                'destination_id': department['DEPARTMENTID']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            department_attributes, self.workspace_id)
        return account_attributes

    def sync_expense_types(self):
        """
        Get expense types
        """
        expense_types = self.connection.expense_types.get_all()

        expense_types_attributes = []

        for expense_type in expense_types:
            expense_types_attributes.append({
                'attribute_type': 'EXPENSE_TYPE',
                'display_name': 'Expense Types',
                'value': expense_type['DESCRIPTION'],
                'destination_id': expense_type['ACCOUNTLABEL']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            expense_types_attributes, self.workspace_id)
        return account_attributes

    def sync_projects(self):
        """
        Get projects
        """
        projects = self.connection.projects.get_all()

        project_attributes = []

        for project in projects:
            project_attributes.append({
                'attribute_type': 'PROJECT',
                'display_name': 'project',
                'value': project['NAME'],
                'destination_id': project['PROJECTID']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            project_attributes, self.workspace_id)
        return account_attributes

    def sync_locations(self):
        """
        Get locations
        """
        locations = self.connection.locations.get_all()

        location_attributes = []

        for location in locations:
            location_attributes.append({
                'attribute_type': 'LOCATION',
                'display_name': 'location',
                'value': location['NAME'],
                'destination_id': location['LOCATIONID']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            location_attributes, self.workspace_id)
        return account_attributes

    def sync_employees(self):
        """
        Get employees
        """
        employees = self.connection.employees.get_all()

        employee_attributes = []

        for employee in employees:
            employee_attributes.append({
                'attribute_type': 'EMPLOYEE',
                'display_name': 'employee',
                'value': employee['CONTACT_NAME'],
                'destination_id': employee['EMPLOYEEID']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            employee_attributes, self.workspace_id)
        return account_attributes

    def sync_vendors(self):
        """
        Get vendors
        """
        vendors = self.connection.vendors.get_all()

        vendor_attributes = []

        for vendor in vendors:
            vendor_attributes.append({
                'attribute_type': 'VENDOR',
                'display_name': 'vendor',
                'value': vendor['NAME'],
                'destination_id': vendor['VENDORID']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            vendor_attributes, self.workspace_id)
        return account_attributes

    def __construct_expense_report(self, expense_report: ExpenseReport, \
        expense_report_lineitems: List[ExpenseReportLineitem]) -> Dict:
        """
        Create a expense report
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        """
        expsense_payload = []
        for lineitem in expense_report_lineitems:
            expense = {
                'expensetype' if lineitem.expense_type_id else 'glaccountno': lineitem.expense_type_id \
                    if lineitem.expense_type_id else lineitem.gl_account_number,
                'amount': lineitem.amount,
                'expensedate': {
                    'year': datetime.strftime(lineitem.spent_at, '%Y'),
                    'month': datetime.strftime(lineitem.spent_at, '%m'),
                    'day': datetime.strftime(lineitem.spent_at, '%d')
                },
                'memo': lineitem.memo,
                'locationid': lineitem.location_id,
                'departmentid': lineitem.department_id,
                'projectid': lineitem.project_id
            }

            expsense_payload.append(expense)

        expense_report_payload = {
            'employeeid': expense_report.employee_id,
            'datecreated': {
                'year': datetime.today().year,
                'month': datetime.today().month,
                'day': datetime.today().day
            },
            'state': 'Submitted',
            'description': '{0} - {1}'.format(expense_report.description['claim_number'], \
                expense_report.description['employee_email']),
            'expenses': {
                'expense': expsense_payload
            }
        }

        return expense_report_payload

    def __construct_bill(self, bill: Bill, bill_lineitems: List[BillLineitem]) -> Dict:
        """
        Create a bill
        :param bill: Bill object extracted from database
        :param bill_lineitems: BillLineItem objects extracted from database
        :return: constructed bill
        """
        bill_lineitems_payload = []
        for lineitem in bill_lineitems:
            expense = {
                'ACCOUNTNO': lineitem.gl_account_number,
                'TRX_AMOUNT': lineitem.amount,
                'LOCATIONID': lineitem.location_id,
                'DEPARTMENTID': lineitem.department_id,
                'PROJECTID': lineitem.project_id
            }

            bill_lineitems_payload.append(expense)

        current_date = '{0}/{1}/{2}'.format(datetime.today().month, datetime.today().day, datetime.today().year)
        bill_payload = {
            'WHENCREATED': current_date,
            'VENDORID': bill.vendor_id,
            'RECORDID': '{0} - {1}'.format(bill.description['claim_number'], bill.description['employee_email']),
            'WHENDUE': current_date,
            'APBILLITEMS': {
                'APBILLITEM': bill_lineitems_payload
            }
        }

        return bill_payload

    def post_expense_report(self, expense_report: ExpenseReport, expense_report_lineitems: List[ExpenseReportLineitem]):
        """
        Post expense report to Sage Intacct
        """
        expense_report_payload = self.__construct_expense_report(expense_report, expense_report_lineitems)
        created_expense_report = self.connection.expense_reports.post(expense_report_payload)
        return created_expense_report

    def post_bill(self, bill: Bill, bill_lineitems: List[BillLineitem]):
        """
        Post expense report to Sage Intacct
        """
        bill_payload = self.__construct_bill(bill, bill_lineitems)
        created_bill = self.connection.bills.post(bill_payload)
        return created_bill

    def update_expense_report(self, object_key, supdocid: str):
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: expense report key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.expense_reports.update_attachment(key=object_key, supdocid=supdocid)

    def update_bill(self, object_key, supdocid: str):
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: expense report key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.bills.update_attachment(recordno=object_key, supdocid=supdocid)

    def post_attachments(self, attachments: List[Dict], claim_number: str):
        """
        Post attachments to Sage Intacct
        :param attachments: attachment[dict()]
        :param claim_number: claim number of the expense group
        :return: supdocid in sage intacct
        """

        if attachments:
            attachment_number = 1
            attachments_list = []
            for attachment in attachments:
                attachment_type = attachment['filename'].split('.')[1]
                attachmentToAppend = {
                    'attachmentname': '{0} - {1}'.format(attachment['expense_id'], attachment_number),
                    'attachmenttype': attachment_type,
                    'attachmentdata': attachment['content']
                }

                attachments_list.append(attachmentToAppend)
                attachment_number = attachment_number + 1

            data = {
                'supdocid': claim_number,
                'supdocfoldername': 'FyleAttachments',
                'attachments': {
                    'attachment': attachments_list
                }
            }

            created_attachment = self.connection.attachments.post(data)

            if created_attachment['status'] == 'success' and created_attachment['key']:
                return claim_number

            return False
