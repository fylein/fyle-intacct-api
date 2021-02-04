from typing import List, Dict
from datetime import datetime

from cryptography.fernet import Fernet

from django.conf import settings

from fyle_accounting_mappings.models import DestinationAttribute

from sageintacctsdk import SageIntacctSDK

from apps.workspaces.models import SageIntacctCredential, WorkspaceGeneralSettings

from .models import ExpenseReport, ExpenseReportLineitem, Bill, BillLineitem, ChargeCardTransaction,\
    ChargeCardTransactionLineitem, APPayment, APPaymentLineitem, SageIntacctReimbursement, \
    SageIntacctReimbursementLineitem


class SageIntacctConnector:
    """
    Sage Intacct utility functions
    """

    def __init__(self, credentials_object: SageIntacctCredential, workspace_id: int):
        sender_id = settings.SI_SENDER_ID
        sender_password = settings.SI_SENDER_PASSWORD
        encryption_key = settings.ENCRYPTION_KEY
        cipher_suite = Fernet(encryption_key)
        decrypted_password = cipher_suite.decrypt(credentials_object.si_user_password.encode('utf-8')).decode('utf-8')

        self.connection = SageIntacctSDK(
            sender_id=sender_id,
            sender_password=sender_password,
            user_id=credentials_object.si_user_id,
            company_id=credentials_object.si_company_id,
            user_password=credentials_object.si_user_password
        )

        self.workspace_id = workspace_id

        credentials_object.save()

    def sync_accounts(self, workspace_id):
        """
        Get accounts
        """
        accounts = self.connection.accounts.get_all()
        general_settings = None
        general_settings: WorkspaceGeneralSettings = WorkspaceGeneralSettings.objects.filter(
            workspace_id=workspace_id).first()

        account_attributes = []

        for account in accounts:
            account_attributes.append({
                'attribute_type': 'ACCOUNT',
                'display_name': 'account',
                'value': account['TITLE'],
                'destination_id': account['ACCOUNTNO']
            })

            if general_settings and general_settings.corporate_credit_card_expenses_object:
                account_attributes.append({
                    'attribute_type': 'CCC_ACCOUNT',
                    'display_name': 'Credit Card Account',
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

    def sync_charge_card_accounts(self):
        """
        Get charge card accounts
        """
        charge_card_accounts = self.connection.charge_card_accounts.get_all()

        charge_card_accounts_attributes = []

        for charge_card_account in charge_card_accounts:
            charge_card_accounts_attributes.append({
                'attribute_type': 'CHARGE_CARD_NUMBER',
                'display_name': 'Charge Card Account',
                'value': charge_card_account['CARDID'],
                'destination_id': charge_card_account['CARDID']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            charge_card_accounts_attributes, self.workspace_id)
        return account_attributes

    def sync_payment_accounts(self):
        """
        Get Payment accounts
        """
        payment_accounts = self.connection.checking_accounts.get_all()['checkingaccount']

        payment_accounts_attributes = []

        for payment_account in payment_accounts:
            payment_accounts_attributes.append({
                'attribute_type': 'PAYMENT_ACCOUNT',
                'display_name': 'Payment Account',
                'value': payment_account['BANKNAME'],
                'destination_id': payment_account['BANKACCOUNTID']
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            payment_accounts_attributes, self.workspace_id)
        return account_attributes

    def sync_projects(self):
        """
        Get projects
        """
        projects = self.connection.projects.get_all()

        project_attributes = []

        for project in projects:
            detail = {
                'CUSTOMERID': project['CUSTOMERID'],
                'CUSTOMERNAME': project['CUSTOMERNAME']
            }

            project_attributes.append({
                'attribute_type': 'PROJECT',
                'display_name': 'project',
                'value': project['NAME'],
                'destination_id': project['PROJECTID'],
                'active': True if project['STATUS'] == 'active' else False,
                'detail': detail
            })

        account_attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            project_attributes, self.workspace_id)
        return account_attributes

    def sync_items(self):
        """
        Get items
        """
        items = self.connection.items.get_all()

        item_attributes = []

        for item in items:
            # remove this check when we are mapping Fyle Categories with Sage Intacct Items
            if item['ITEMTYPE'] == 'Non-Inventory':
                item_attributes.append({
                    'attribute_type': 'ITEM',
                    'display_name': 'item',
                    'value': item['NAME'],
                    'destination_id': item['ITEMID']
                })

        attributes = DestinationAttribute.bulk_upsert_destination_attributes(
            item_attributes, self.workspace_id)
        return attributes

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

    def sync_vendors(self, workspace_id: str):
        """
        Get vendors
        """
        vendors = self.connection.vendors.get_all()

        vendor_attributes = []
        general_settings = None
        general_settings: WorkspaceGeneralSettings = WorkspaceGeneralSettings.objects.filter(
            workspace_id=workspace_id).first()

        for vendor in vendors:
            vendor_attributes.append({
                'attribute_type': 'VENDOR',
                'display_name': 'vendor',
                'value': vendor['NAME'],
                'destination_id': vendor['VENDORID']
            })

            if general_settings and general_settings.corporate_credit_card_expenses_object == 'BILL':
                vendor_attributes.append({
                    'attribute_type': 'CHARGE_CARD_NUMBER',
                    'display_name': 'Charge Card Account',
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
            transaction_date = datetime.strptime(expense_report.transaction_date, '%Y-%m-%dT%H:%M:%S')
            expense = {
                'expensetype' if lineitem.expense_type_id else 'glaccountno': lineitem.expense_type_id \
                    if lineitem.expense_type_id else lineitem.gl_account_number,
                'amount': lineitem.amount,
                'expensedate': {
                    'year': transaction_date.year,
                    'month': transaction_date.month,
                    'day': transaction_date.day
                },
                'memo': lineitem.memo,
                'locationid': lineitem.location_id,
                'departmentid': lineitem.department_id,
                'projectid': lineitem.project_id,
                'customerid': lineitem.customer_id,
                'itemid': lineitem.item_id,
                'billable': lineitem.billable
            }

            expsense_payload.append(expense)

        transaction_date = datetime.strptime(expense_report.transaction_date, '%Y-%m-%dT%H:%M:%S')
        expense_report_payload = {
            'employeeid': expense_report.employee_id,
            'datecreated': {
                'year': transaction_date.year,
                'month': transaction_date.month,
                'day': transaction_date.day
            },
            'state': 'Submitted',
            'description': expense_report.memo,
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
                'ENTRYDESCRIPTION': lineitem.memo,
                'LOCATIONID': lineitem.location_id,
                'DEPARTMENTID': lineitem.department_id,
                'PROJECTID': lineitem.project_id,
                'CUSTOMERID': lineitem.customer_id,
                'ITEMID': lineitem.item_id,
                'BILLABLE': lineitem.billable
            }

            bill_lineitems_payload.append(expense)

        transaction_date = datetime.strptime(bill.transaction_date, '%Y-%m-%dT%H:%M:%S')
        transaction_date = '{0}/{1}/{2}'.format(transaction_date.month, transaction_date.day, transaction_date.year)
        current_date = '{0}/{1}/{2}'.format(datetime.today().month, datetime.today().day, datetime.today().year)

        bill_payload = {
            'WHENCREATED': transaction_date,
            'VENDORID': bill.vendor_id,
            'RECORDID': bill.memo,
            'WHENDUE': current_date,
            'APBILLITEMS': {
                'APBILLITEM': bill_lineitems_payload
            }
        }

        return bill_payload

    def __construct_charge_card_transaction(self, charge_card_transaction: ChargeCardTransaction, \
                                            charge_card_transaction_lineitems: List[
                                                ChargeCardTransactionLineitem]) -> Dict:
        """
        Create a charge card transaction
        :param charge_card_transaction: ChargeCardTransaction object extracted from database
        :param charge_card_transaction_lineitems: ChargeCardTransactionLineitem objects extracted from database
        :return: constructed charge_card_transaction
        """
        charge_card_transaction_payload = []
        for lineitem in charge_card_transaction_lineitems:
            expense = {
                'glaccountno': lineitem.gl_account_number,
                'description': lineitem.memo,
                'paymentamount': lineitem.amount,
                'departmentid': lineitem.department_id,
                'locationid': lineitem.location_id,
                'customerid': lineitem.customer_id,
                'projectid': lineitem.project_id,
                'itemid': lineitem.item_id
            }

            charge_card_transaction_payload.append(expense)

        transaction_date = datetime.strptime(charge_card_transaction.transaction_date, '%Y-%m-%dT%H:%M:%S')
        charge_card_transaction_payload = {
            'chargecardid': charge_card_transaction.charge_card_id,
            'paymentdate': {
                'year': transaction_date.year,
                'month': transaction_date.month,
                'day': transaction_date.day
            },
            'description': charge_card_transaction.memo,
            'ccpayitems': {
                'ccpayitem': charge_card_transaction_payload
            }
        }

        return charge_card_transaction_payload

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

    def get_bill(self, bill_id):
        """
        GET bill from SAGE
        """
        bill = self.connection.bills.get_by_id(bill_id)
        return bill

    def post_charge_card_transaction(self, charge_card_transaction: ChargeCardTransaction, \
                                     charge_card_transaction_lineitems: List[ChargeCardTransactionLineitem]):
        """
        Post charge card transaction to Sage Intacct
        """
        created_charge_card_transaction_payload = self.__construct_charge_card_transaction \
            (charge_card_transaction, charge_card_transaction_lineitems)
        created_charge_card_transaction = self.connection.charge_card_transactions.post \
            (created_charge_card_transaction_payload)
        return created_charge_card_transaction

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

    def update_charge_card_transaction(self, object_key, supdocid: str):
        """
        Map posted attachment with Sage Intacct Object
        :param object_key: charge card transaction key
        :param supdocid: attachments id
        :return: response from sage intacct
        """
        return self.connection.charge_card_transactions.update_attachment(key=object_key, supdocid=supdocid)

    def post_attachments(self, attachments: List[Dict], supdoc_id: str):
        """
        Post attachments to Sage Intacct
        :param attachments: attachment[dict()]
        :param supdoc_id: supdoc id
        :return: supdocid in sage intacct
        """

        if attachments:
            attachment_number = 1
            attachments_list = []
            for attachment in attachments:
                attachment_type = attachment['filename'].split('.')[1]
                attachment_to_append = {
                    'attachmentname': '{0} - {1}'.format(attachment['expense_id'], attachment_number),
                    'attachmenttype': attachment_type,
                    'attachmentdata': attachment['content']
                }

                attachments_list.append(attachment_to_append)
                attachment_number = attachment_number + 1

            data = {
                'supdocid': supdoc_id,
                'supdocfoldername': 'FyleAttachments',
                'attachments': {
                    'attachment': attachments_list
                }
            }

            created_attachment = self.connection.attachments.post(data)

            if created_attachment['status'] == 'success' and created_attachment['key']:
                return supdoc_id

            return False

    @staticmethod
    def __construct_ap_payment(ap_payment: APPayment, ap_payment_lineitems: List[APPaymentLineitem]) -> Dict:
        """
        Create an AP Payment
        :param ap_payment: APPayment object extracted from database
        :param ap_payment_lineitems: APPaymentLineItem objects extracted from database
        :return: constructed AP Payment
        """

        ap_payment_lineitems_payload = []

        for lineitem in ap_payment_lineitems:
            payment_detail = {
                'RECORDKEY': lineitem.record_key,
                'TRX_PAYMENTAMOUNT': lineitem.amount
            }

            ap_payment_lineitems_payload.append(payment_detail)

        current_date = '{0}/{1}/{2}'.format(datetime.today().month, datetime.today().day, datetime.today().year)

        ap_payment_payload = {
            'FINANCIALENTITY': ap_payment.payment_account_id,
            'PAYMENTMETHOD': 'Cash',
            'VENDORID': ap_payment.vendor_id,
            'DESCRIPTION': ap_payment.description,
            'PAYMENTDATE': current_date,
            'APPYMTDETAILS': {
                'APPYMTDETAIL': ap_payment_lineitems_payload
            }
        }

        return ap_payment_payload

    def post_ap_payment(self, ap_payment: APPayment, ap_payment_lineitems: List[APPaymentLineitem]):
        """
        Post AP Payment to Sage Intacct
        """
        ap_payment_payload = self.__construct_ap_payment(ap_payment, ap_payment_lineitems)
        print('AP Payment Payload - ', ap_payment_payload)
        # created_ap_payment = self.connection.ap_payments.post(ap_payment_payload)
        # return created_ap_payment

    @staticmethod
    def __construct_sage_intacct__reimbursement(reimbursement: SageIntacctReimbursement,
                                  reimbursement_lineitems: List[SageIntacctReimbursementLineitem]) -> Dict:
        """
        Create a Reimbursement
        :param reimbursement: Reimbursement object extracted from database
        :param reimbursement_lineitems: ReimbursementLineItem objects extracted from database
        :return: constructed Reimbursement
        """

        reimbursement_lineitems_payload = []

        for lineitem in reimbursement_lineitems:
            reimbursement_detail = {
                'key': lineitem.record_key,
                'paymentamount': lineitem.amount
            }

            reimbursement_lineitems_payload.append(reimbursement_detail)

        current_date = '{0}/{1}/{2}'.format(datetime.today().month, datetime.today().day, datetime.today().year)

        reimbursement_payload = {
            'bankaccountid': reimbursement.account_id,
            'employeeid': reimbursement.employee_id,
            'memo': reimbursement.memo,
            'paymentmethod': 'Cash',
            'paymentdescription': reimbursement.payment_description,
            'paymentdate': current_date,
            'eppaymentrequestitems': {
                'eppaymentrequestitem': reimbursement_lineitems_payload
            }
        }

        return reimbursement_payload

    def post_sage_intacct_reimbursement(self, reimbursement: SageIntacctReimbursement,
                                        reimbursement_lineitems: List[SageIntacctReimbursementLineitem]):
        """
        Post Reimbursement to Sage Intacct
        """
        reimbursement_payload = self.__construct_sage_intacct__reimbursement(reimbursement, reimbursement_lineitems)
        print('Reimbursement Payload - ', reimbursement_payload)
        # created_reimbursement = self.connection.reimbursements.post(reimbursement_payload)
        # return created_reimbursement
