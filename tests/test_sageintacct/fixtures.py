data = {
    'bill_payload': {'WHENCREATED': '9/28/2022', 'SUPDOCID': None, 'VENDORID': 'Ashwin', 'RECORDID': 'Reimbursable expense - C/2022/09/R/21', 'WHENDUE': '9/28/2022', 'BASECURR': 'USD', 'CURRENCY': 'USD', 'EXCH_RATE_TYPE_ID': None, 'APBILLITEMS': {'APBILLITEM': [{'CLASS': 'sample', 'ACCOUNTNO': '20100', 'TRX_AMOUNT': 0.0, 'TOTALTRXAMOUNT': 21.0, 'TASKID': None, 'COSTTYPEID': None, 'ENTRYDESCRIPTION': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/21 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txR9dyrqr1Jn?org_id=or79Cob97KSh', 'LOCATIONID': '600', 'DEPARTMENTID': '300', 'PROJECTID': '10061', 'CUSTOMERID': '10061', 'ITEMID': None, 'CLASSID': '600', 'BILLABLE': False, 'TAXENTRIES': {'TAXENTRY': {'DETAILID': 'Capital Goods Imported'}}, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txR9dyrqr1Jn?org_id=or79Cob97KSh'}]}, 'INCLUSIVETAX': True, 'TAXSOLUTIONID': 'South Africa - VAT'}]}},
    'expense_report_payload': {
        'employeeid': 'Joanna',
        'datecreated': {'year': 2022, 'month': 9, 'day': 28},
        'state': 'Submitted',
        'description': 'Reimbursable expense - C/2022/09/R/21',
        'basecurr': 'USD', 'currency': 'USD',
        'supdocid': None,
        'expenses': {
            'expense': [
                {
                    'CLASS': 'sample',
                    'glaccountno': '20100',
                    'amount': 0.0,
                    'expensedate': {'year': 2022, 'month': 9, 'day': 20}, 
                    'memo': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/21 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txR9dyrqr1Jn?org_id=or79Cob97KSh', 
                    'totaltrxamount': 21.0, 
                    'locationid': '600', 
                    'departmentid': '300', 
                    'projectid': '10061', 
                    'customerid': '10061', 
                    'itemid': None,
                    'classid': '600',
                    'taskid': None, 
                    'costtypeid': None, 
                    'billable': False, 
                    'exppmttype': '', 
                    'taxentries': {'taxentry': {'detailid': 'Capital Goods Imported'}}, 
                    'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txR9dyrqr1Jn?org_id=or79Cob97KSh'}]}
                    }
            ]
        },
        'inclusivetax': True,
        'taxsolutionid': 'South Africa - VAT'
    },
    'journal_entry_payload':{'recordno': None, 'journal': 'FYLE_JE', 'batch_date': '9/28/2022', 'batch_title': 'Corporate Credit Card expense - C/2022/09/R/22 - 28/09/2022', 'supdocid': None, 'entries': [{'glentry': [{'CLASS': 'sample', 'accountno': '20100', 'currency': 'USD', 'amount': 11.0, 'tr_type': -1, 'description': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh', 'department': '300', 'location': '600', 'projectid': '10061', 'customerid': '10061', 'vendorid': 'Ashwin', 'employeeid': None, 'itemid': '1012', 'classid': '600', 'billable': True, 'taskid': None, 'costtypeid': None, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'}]}}, {'accountno': '20100', 'currency': 'USD', 'amount': 11.0, 'tr_type': 1, 'description': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh', 'department': '300', 'location': '600', 'projectid': '10061', 'customerid': '10061', 'vendorid': 'Ashwin', 'employeeid': None, 'itemid': '1012', 'classid': '600', 'taskid': None, 'costtypeid': None, 'billable': True, 'taxentries': {'taxentry': {'trx_tax': None, 'detailid': '4'}}, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'}]}}]}], 'taximplications': 'Inbound', 'taxsolutionid': 'South Africa - VAT'},
    'journal_entry_re_payload':{'recordno': None, 'journal': 'FYLE_JE', 'batch_date': '9/28/2022', 'batch_title': 'Reimbursable expense - C/2022/09/R/21 - 28/09/2022', 'supdocid': None, 'entries': [{'glentry': [{'CLASS': 'sample', 'accountno': '20100', 'currency': 'USD', 'amount': 11.0, 'tr_type': -1, 'description': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/21 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh', 'department': '300', 'location': '600', 'projectid': '10061', 'customerid': '10061', 'vendorid': 'Ashwin', 'employeeid': None, 'itemid': '1012', 'classid': '600', 'billable': True, 'taskid': None, 'costtypeid': None, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'}]}}, {'accountno': '20100', 'currency': 'USD', 'amount': 11.0, 'tr_type': 1, 'description': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh', 'department': '300', 'location': '600', 'projectid': '10061', 'customerid': '10061', 'vendorid': 'Ashwin', 'employeeid': None, 'itemid': '1012', 'classid': '600', 'taskid': None, 'costtypeid': None, 'billable': True, 'taxentries': {'taxentry': {'trx_tax': None, 'detailid': '4'}}, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'}]}}]}], 'taximplications': 'Inbound', 'taxsolutionid': 'South Africa - VAT'},
    'journal_entry_payload_refund':{'recordno': None, 'journal': 'FYLE_JE', 'batch_date': '9/28/2022', 'batch_title': 'Corporate Credit Card expense - C/2022/09/R/22 - 28/09/2022', 'supdocid': None, 'entries': [{'glentry': [{'CLASS': 'sample', 'accountno': '20100', 'currency': 'USD', 'amount': 11.0, 'tr_type': -1, 'description': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh', 'department': '300', 'location': '600', 'projectid': '10061', 'customerid': '10061', 'vendorid': 'Ashwin', 'employeeid': None, 'itemid': '1012', 'classid': '600', 'taskid': None, 'costtypeid': None, 'billable': True, 'taxentries': {'taxentry': {'trx_tax': None, 'detailid': '4'}}, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'}]}}, {'accountno': '20100', 'currency': 'USD', 'amount': 11.0, 'tr_type': 1, 'description': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh', 'department': '300', 'location': '600', 'projectid': '10061', 'customerid': '10061', 'vendorid': 'Ashwin', 'employeeid': None, 'itemid': '1012', 'classid': '600', 'taskid': None, 'costtypeid': None, 'billable': True, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'}]}}]}], 'taximplications': 'Inbound', 'taxsolutionid': 'South Africa - VAT'},
    'ap_payment_payload':{'FINANCIALENTITY': '400_CHK', 'PAYMENTMETHOD': 'Cash', 'VENDORID': 'Ashwin', 'DESCRIPTION': 'Payment for Bill - C/2022/09/R/21', 'PAYMENTDATE': '9/28/2022', 'CURRENCY': 'USD', 'BASECURR': 'USD', 'APPYMTDETAILS': {'APPYMTDETAIL': [{'RECORDKEY': '3032', 'TRX_PAYMENTAMOUNT': 21.0}]}},
    'charge_card_transaction_payload': {'chargecardid': 'sample', 'supdocid': None, 'paymentdate': {'year': 2022, 'month': 9, 'day': 20}, 'referenceno': 'E/2022/09/T/22', 'payee': 'Ashwin', 'description': 'Corporate Credit Card expense - C/2022/09/R/22 - 28/09/2022', 'currency': 'USD', 'exchratetype': None, 'inclusivetax': True, 'ccpayitems': {'ccpayitem': [{'glaccountno': '20100', 'description': 'ashwin.t@fyle.in - Food - 2022-09-20 - C/2022/09/R/22 -  - https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh', 'paymentamount': 0.0, 'departmentid': '300', 'locationid': '600', 'customerid': '10061', 'vendorid': 'Ashwin', 'projectid': '10061', 'itemid': '1012', 'classid': '600', 'taskid': None, 'costtypeid': None, 'customfields': {'customfield': [{'customfieldname': 'FYLE_EXPENSE_URL', 'customfieldvalue': 'https://staging.fyle.tech/app/admin/#/enterprise/view_expense/txCqLqsEnAjf?org_id=or79Cob97KSh'}, {'customfieldname': 'USERDIM1', 'customfieldvalue': 'C000013'}]}, 'totaltrxamount': 11.0, 'taxentries': {'taxentry': {'detailid': 'Capital Goods Imported'}}}]}},
    'sage_intacct_reimbursement_payload':{'bankaccountid': '400_CHK', 'employeeid': 'Joanna', 'memo': 'Payment for Expense Report - C/2022/09/R/21', 'paymentmethod': 'Cash', 'paymentdate': {'year': '2022', 'month': '09', 'day': '28'}, 'eppaymentrequestitems': {'eppaymentrequestitem': [{'key': '3032', 'paymentamount': 21.0}]}, 'paymentdescription': 'Payment for Expense Report by ashwin.t@fyle.in'},
    'journal_entry_response': {
        'data': {
            'glbatch': {
                'RECORD_URL': 'https://www-p02.intacct.com/ia/acct/ur.phtml?.r=cADOKmBnspC0Y1Mp5umhgD3e2gD3B_6rV45dIYv59zw',
                '#text': '...',
                'RECORDNO': 6679,
                'BATCHNO': 249,
                'BATCH_TITLE': 'Paying some folks',
                'BALANCE': '',
                'JOURNAL': 'GJ',
                'JOURNALKEY': 5,
                'JOURNAL_BILLABLE': '',
                'ADJ': 'F',
                'BATCH_DATE': '01/09/2019',
                'MODULE': '2.GL',
                'CHILDENTITY': '',
                'USERKEY': 20,
                'REFERENCENO': '',
                'REVERSED': '',
                'REVERSEDKEY': '',
                'REVERSEDFROM': '',
                'TEMPLATEKEY': '',
                'PRBATCHKEY': '',
                'PRBATCHRECTYPE': '',
                'MODIFIED': '01/09/2019 22:01:29',
                'MODIFIEDBYID': 'jsmith',
                'SCHOPKEY': '',
                'RRSENTRYKEY': '',
                'RRSKEY': '',
                'CONTRACTSCHEDULEENTRYKEY': '',
                'CONTRACTSCHEDULEKEY': '',
                'GLACCTALLOCATIONRUNKEY': '',
                'BASELOCATION': 1,
                'BASELOCATION_NO': 100,
                'BASELOCATION_NAME': 'ACME USA',
                'USERINFO.LOGINID': 'jsmith',
                'LOCATIONKEY': '',
                'WHENCREATED': '01/09/2019 22:01:29',
                'WHENMODIFIED': '01/09/2019 22:01:29',
                'CREATEDBY': 20,
                'MODIFIEDBY': 20,
                'STATE': 'Submitted'
            }
        }
    },
    'bill_response': {'status': 'success', 'function': 'create', 'controlid': 'a1a61e97-8a53-4390-a5f8-b1d628b2e83b', 'data': {'@listtype': 'objects', '@count': '1', 'apbill': {'RECORDNO': '3430', 'RECORD_URL': 'https://www-p02.intacct.com/ia/acct/ur.phtml?.r=cADOKmBnspC0Y1Mp5umhgD3e2gD3B_6rV45dIYv59zw',}}},
    'credit_card_response': {'key': '3430', 'status': 'success', 'function': 'create', 'controlid': 'a1a61e97-8a53-4390-a5f8-b1d628b2e83b', 'data': {'@listtype': 'objects', '@count': '1', 'cctransaction': {'RECORDNO': '3430', 'RECORD_URL': 'https://www-p02.intacct.com/ia/acct/ur.phtml?.r=cADOKmBnspC0Y1Mp5umhgD3e2gD3B_6rV45dIYv59zw',}}},
    'expense_report_post_response': {'status': 'success', 'function': 'create_expensereport', 'controlid': 'a1a61e97-8a53-4390-a5f8-b1d628b2e83b','key': '3430'},
    'expense_report_response': {'status': 'success', 'function': 'create', 'controlid': 'a1a61e97-8a53-4390-a5f8-b1d628b2e83b', 'data': {'@listtype': 'objects', '@count': '1', 'eexpenses': {'RECORDNO': '3430', 'RECORD_URL': 'https://www-p02.intacct.com/ia/acct/ur.phtml?.r=cADOKmBnspC0Y1Mp5umhgD3e2gD3B_6rV45dIYv59zw', 'STATE': 'Paid'}}},
    'create_contact': {
        'Contacts': [{
            'ContactID': '79c88297-27fb-4f6f-87a8-fe27017031c6',
            'ContactStatus': 'ACTIVE',
            'Name': 'sample',
            'FirstName': 'sample',
            'LastName': '',
            'EmailAddress': 'sample@fyle.in',
            'BankAccountDetails': '',
            'Addresses': [
                {
                    'AddressType': 'STREET',
                    'City': '',
                    'Region': '',
                    'PostalCode': '',
                    'Country': ''
                },
                {
                    'AddressType': 'POBOX',
                    'City': '',
                    'Region': '',
                    'PostalCode': '',
                    'Country': ''
                }
            ],
            'Phones': [
                {
                    'PhoneType': 'DEFAULT',
                    'PhoneNumber': '',
                    'PhoneAreaCode': '',
                    'PhoneCountryCode': ''
                },
                {
                    'PhoneType': 'DDI',
                    'PhoneNumber': '',
                    'PhoneAreaCode': '',
                    'PhoneCountryCode': ''
                },
                {
                    'PhoneType': 'FAX',
                    'PhoneNumber': '',
                    'PhoneAreaCode': '',
                    'PhoneCountryCode': ''
                },
                {
                    'PhoneType': 'MOBILE',
                    'PhoneNumber': '',
                    'PhoneAreaCode': '',
                    'PhoneCountryCode': ''
                }
            ],
            'UpdatedDateUTC': '/Date(1660754701320+0000)/',
            'ContactGroups': [

            ],
            'IsSupplier':False,
            'IsCustomer':False,
            'SalesTrackingCategories':[

            ],
            'PurchasesTrackingCategories':[

            ],
            'ContactPersons':[

            ],
            'HasValidationErrors':False
        }]
    },
    'reimbursements': [
        {
            'amount': 76,
            'code': None,
            'created_at': '2022-01-20T16:30:44.584100',
            'creator_user_id': 'usqywo0f3nBY',
            'currency': 'USD',
            'id': 'reimgCW1Og0BcM',
            'is_exported': False,
            'is_paid': False,
            'mode': 'OFFLINE',
            'org_id': 'orsO0VW86WLQ',
            'paid_at': None,
            'purpose': 'C/2022/01/R/2;Ashwin',
            'reimbursement_number': 'P/2022/01/R/2',
            'settlement_id': 'setrunCck8hLH',
            'updated_at': '2022-01-20T16:30:44.584100',
            'user_id': 'usqywo0f3nBY',
        },
        {
            'amount': 76,
            'code': None,
            'created_at': '2022-01-20T16:30:44.584100',
            'creator_user_id': 'usqywo0f3nBY',
            'currency': 'USD',
            'id': 'reimgCW1Og0BcM',
            'is_exported': False,
            'is_paid': False,
            'mode': 'OFFLINE',
            'org_id': 'orsO0VW86WLQ',
            'paid_at': None,
            'purpose': 'C/2022/01/R/2;Ashwin',
            'reimbursement_number': 'P/2022/01/R/3',
            'settlement_id': 'setrunCck8hLH',
            'updated_at': '2022-01-20T16:30:44.584100',
            'user_id': 'usqywo0f3nBY',
        },
        {
            'amount': 76,
            'code': None,
            'created_at': '2022-01-20T16:30:44.584100',
            'creator_user_id': 'usqywo0f3nBY',
            'currency': 'USD',
            'id': 'reimgCW1Og0BcM',
            'is_exported': False,
            'is_paid': False,
            'mode': 'OFFLINE',
            'org_id': 'orsO0VW86WLQ',
            'paid_at': None,
            'purpose': 'C/2022/01/R/2;Ashwin',
            'reimbursement_number': 'P/2022/01/R/4',
            'settlement_id': 'setlpIUKpdvsT',
            'updated_at': '2022-01-20T16:30:44.584100',
            'user_id': 'usqywo0f3nBY',
        },
        {
            'amount': 76,
            'code': None,
            'created_at': '2022-01-20T16:30:44.584100',
            'creator_user_id': 'usqywo0f3nBY',
            'currency': 'USD',
            'id': 'reimgCW1Og0BcM',
            'is_exported': False,
            'is_paid': False,
            'mode': 'OFFLINE',
            'org_id': 'orsO0VW86WLQ',
            'paid_at': None,
            'purpose': 'C/2022/01/R/2;Ashwin',
            'reimbursement_number': 'P/2022/01/R/5',
            'settlement_id': 'set33iAVXO7BA',
            'updated_at': '2022-01-20T16:30:44.584100',
            'user_id': 'usqywo0f3nBY',
        },
    ],
    'get_bill': {'@listtype': 'apbill', '@count': '1', '@totalcount': '1', '@numremaining': '0', '@resultId': '', 'apbill': {'STATE': 'Paid', 'RECORD_URL': 'https://www-p02.intacct.com/ia/acct/ur.phtml?.r=cADOKmBnspC0Y1Mp5umhgD3e2gD3B_6rV45dIYv59zw'}},
    'get_all_organisations': [
        {
            'Addresses': [
                {
                    'AddressLine1': '23 Main Street',
                    'AddressLine2': 'Central City',
                    'AddressType': 'POBOX',
                    'AttentionTo': '',
                    'City': 'Marineville',
                    'Country': '',
                    'PostalCode': '12345',
                    'Region': ''
                }
            ],
            'BaseCurrency': 'USD',
            'Class': 'DEMO',
            'CountryCode': 'CA',
            'CreatedDateUTC': '/Date(1661500186077)/',
            'DefaultPurchasesTax': 'Remember previous',
            'DefaultSalesTax': 'Remember previous',
            'Edition': 'BUSINESS',
            'ExternalLinks': [],
            'FinancialYearEndDay': 31,
            'FinancialYearEndMonth': 12,
            'IsDemoCompany': True,
            'LegalName': 'Demo Company (Global)',
            'Name': 'Demo Company (Global)',
            'OrganisationEntityType': 'COMPANY',
            'OrganisationID': '25d7b4cd-ed1c-4c5c-80e5-c058b87db8a1',
            'OrganisationStatus': 'ACTIVE',
            'OrganisationType': 'COMPANY',
            'PaymentTerms': {},
            'PaysTax': True,
            'PeriodLockDate': '/Date(1222732800000+0000)/',
            'Phones': [
                {
                    'PhoneAreaCode': '800',
                    'PhoneNumber': '1234 5678',
                    'PhoneType': 'OFFICE'
                }
            ],
            'SalesTaxBasis': 'ACCRUALS',
            'SalesTaxPeriod': '3MONTHLY',
            'ShortCode': '!FR6KJ',
            'TaxNumber': '101-2-303',
            'TaxNumberName': 'Tax reg',
            'Timezone': 'EASTERNSTANDARDTIME',
            'Version': 'GLOBAL'
        }
    ],
    'get_projects':[
        {
            'RECORDNO':'111',
            'PROJECTID':'10064',
            'NAME':'Direct Mail Campaign',
            'DESCRIPTION':'None',
            'CURRENCY':'AUD',
            'PROJECTCATEGORY':'Contract',
            'PROJECTSTATUS':'In Progress',
            'PARENTKEY':'None',
            'PARENTID':'None',
            'PARENTNAME':'None',
            'STATUS':'active',
            'CUSTOMERKEY':'42',
            'CUSTOMERID':'10064',
            'CUSTOMERNAME':'Med dot',
            'PROJECTTYPE':'AMP-Marketing',
            'DEPARTMENTNAME':'Services',
            'LOCATIONID':'600',
            'LOCATIONNAME':'Australia',
            'BUDGETID':'None',
            'MEGAENTITYID':'600',
            'MEGAENTITYNAME':'Australia'
        }
    ],
    'get_departments':[
        {
            'RECORDNO':'3',
            'DEPARTMENTID':'300',
            'TITLE':'Admin',
            'PARENTKEY':'None',
            'PARENTID':'None',
            'SUPERVISORNAME':'Tesla, Nikki',
            'STATUS':'active',
            'CUSTTITLE':'None'
        }
    ],
    'get_charge_card_accounts':[
        {
            'RECORDNO':'3',
            'CARDID':'Charge Card 1',
            'DESCRIPTION':'None',
            'CARDTYPE':'Visa',
            'EXP_MONTH':'January',
            'EXP_YEAR':'2021',
            'COMMCARD':'C',
            'STATUS':'active',
            'VENDORID':'20003',
            'DEPT':'None',
            'LOCATION':'None',
            'LIABILITYTYPE':'Credit',
            'OUTSOURCECARD':'None'
        }
    ],
    'get_classes':[
        {
            'NAME':'Small Business',
            'CLASSID':'400'
        }
    ],
    'get_expense_payment_types':[
        {
            'RECORDNO':'1',
            'NAME':'Company Credit Card',
            'DESCRIPTION':'None',
            'NONREIMBURSABLE':'true',
            'OFFSETACCTNO':'None',
            'OFFSETACCTTITLE':'None',
            'STATUS':'active',
            'WHENCREATED':'03/03/2020 20:27:09',
            'WHENMODIFIED':'03/03/2020 20:27:09',
            'CREATEDBY':'8',
            'MODIFIEDBY':'8',
            'MEGAENTITYKEY':'None',
            'MEGAENTITYID':'None',
            'MEGAENTITYNAME':'None'
        }
    ],
    'get_location_entities':[
        {
            'RECORDNO':'9',
            'LOCATIONID':'600',
            'NAME':'Australia',
            'REPORTPRINTAS':'None',
            'SUPERVISORID':'None',
            'FIRSTMONTH':'1',
            'FIRSTMONTHTAX':'None',
            'WEEKSTART':'None',
            'FEDERALID':'10-0000351',
            'STARTDATE':'None',
            'ENDDATE':'None',
            'STATUS':'active',
            'HAS_IE_RELATION':'false',
            'CUSTOMERID':'None',
            'CUSTOMERNAME':'None',
            'VENDORID':'None',
            'VENDORNAME':'None',
            'CURRENCY':'AUD',
            'TAXID':'51976067581',
            'ENABLELEGALCONTACT':'false',
            'LEGALNAME':'None',
            'LEGALADDRESS1':'None',
            'LEGALADDRESS2':'None',
            'LEGALCITY':'None',
            'LEGALSTATE':'None',
            'LEGALZIPCODE':'None',
            'LEGALCOUNTRY':'None',
            'OPCOUNTRY':'Australia',
            'ADDRESSCOUNTRYDEFAULT':'Australia',
            'RECORD_URL':'https://www-p02.intacct.com/ia/acct/ur.phtml?.r=5jqUgbnTPWSyfcQt2WN8R_O-Kf-mmZi3S99kptb_bT0'
        }
    ],
    'get_locations':[
        {
            'RECORDNO':'9',
            'LOCATIONID':'600',
            'NAME':'Australia',
            'PARENTID':'None',
            'STATUS':'active',
            'CURRENCY':'AUD'
        }
    ],
    'get_payment_accounts':[
        {
            'BANKACCOUNTID':'500_CHK',
            'BANKACCOUNTNO':'525751035443',
            'GLACCOUNTNO':'10050',
            'BANKNAME':'Demo Bank',
            'ROUTINGNO':'121010303',
            'BRANCHID':'101/1',
            'BANKACCOUNTTYPE':'checking',
            'DEPARTMENTID':'None',
            'LOCATIONID':'500',
            'STATUS':'active',
            'RECORDNO':'10',
            'ACHBANKID':'None',
            'COMPANYNAME':'None'
        }
    ],
    'get_tax_details':[
        {
            'RECORDNO':'78',
            'DETAILID':'UK Import Services Zero Rate',
            'TAXUID':'GB.EXInputServices_GB.ZeroGB.VAT',
            'DESCRIPTION':'UK Import Services Zero Rate',
            'TAXTYPE':'Purchase',
            'VALUE':'0',
            'MINTAXABLE':'None',
            'MAXTAXABLE':'None',
            'INCLUDE':'None',
            'MINTAX':'None',
            'MAXTAX':'None',
            'GLACCOUNT':'12620',
            'TAXAUTHORITY':'None',
            'STATUS':'active',
            'REVERSECHARGE':'false',
            'TAXRATE':'Zero',
            'TAXSOLUTIONID':'United Kingdom - VAT',
            'MEGAENTITYKEY':'None',
            'MEGAENTITYID':'None',
            'MEGAENTITYNAME':'None'
        }
    ],
    'get_dimensions':[
        {
            'objectName':'DEPARTMENT',
            'objectLabel':'Department',
            'termLabel':'Department',
            'userDefinedDimension':'false',
            'enabledInGL':'true'
        }
    ],
    'get_accounts':[
        {
            'RECORDNO':'287',
            'ACCOUNTNO':'16200',
            'TITLE':'Patents & Licenses',
            'ACCOUNTTYPE':'balancesheet',
            'NORMALBALANCE':'debit',
            'CLOSINGTYPE':'non-closing account',
            'STATUS':'active',
            'CATEGORY':'Patents',
            'ALTERNATIVEACCOUNT':'None'
        }
    ],
    'get_employees':[
        {
            'RECORDNO':'6',
            'EMPLOYEEID':'1005',
            'SSN':'246602649',
            'TITLE':'Project Manager',
            'LOCATIONID':'None',
            'DEPARTMENTID':'100',
            'BIRTHDATE':'11/11/1982',
            'STARTDATE':'08/17/2014',
            'ENDDATE':'None',
            'STATUS':'active',
            'EMPLOYEETYPE':'Full Time',
            'EMPLOYEETYPE1099TYPE':'None',
            'GENDER':'male',
            'TERMINATIONTYPE':'None',
            'CONTACT_NAME':'Franco, Ryan',
            'CONTACT.CONTACTNAME':'Franco, Ryan',
            'CONTACT.PREFIX':'None',
            'CONTACT.FIRSTNAME':'Ryan',
            'CONTACT.INITIAL':'None',
            'CONTACT.LASTNAME':'Franco',
            'CONTACT.COMPANYNAME':'None',
            'CONTACT.PRINTAS':'Franco, Ryan',
            'CONTACT.PHONE1':'415-468-5786',
            'CONTACT.PHONE2':'None',
            'CONTACT.CELLPHONE':'None',
            'CONTACT.PAGER':'None',
            'CONTACT.FAX':'None',
            'CONTACT.EMAIL1':'ryan@demo.com',
            'CONTACT.EMAIL2':'None',
            'CONTACT.URL1':'None',
            'CONTACT.URL2':'None',
            'CONTACT.MAILADDRESS.ADDRESS1':'12401 Clinton Ave',
            'CONTACT.MAILADDRESS.ADDRESS2':'None',
            'CONTACT.MAILADDRESS.CITY':'NY',
            'CONTACT.MAILADDRESS.STATE':'NY',
            'CONTACT.MAILADDRESS.ZIP':'10010',
            'CONTACT.MAILADDRESS.COUNTRY':'United States',
            'CONTACT.MAILADDRESS.COUNTRYCODE':'US',
            'CURRENCY':'None',
            'WHENCREATED':'02/10/2020 19:57:41',
            'WHENMODIFIED':'03/03/2020 19:03:33',
            'PAYMETHODKEY':'None',
            'CONTACTKEY':'31',
            'MEGAENTITYKEY':'None',
            'MEGAENTITYID':'None',
            'MEGAENTITYNAME':'None'
        }
    ],
    'get_customers':[
        {
            'NAME':'AB SQUARE',
            'CUSTOMERID':'10001'
        }
    ],
    'get_vendors':[
        {
            'RECORDNO':'51',
            'NAME':'Ashwin',
            'VENDORID':'Ashwin',
            'PARENTKEY':'None',
            'PARENTID':'None',
            'PARENTNAME':'None',
            'DISPLAYCONTACT.CONTACTNAME':'Ashwin(VAshwin)',
            'DISPLAYCONTACT.COMPANYNAME':'Ashwin',
            'DISPLAYCONTACT.FIRSTNAME':'FyleT',
            'DISPLAYCONTACT.LASTNAME':'FyleT',
            'DISPLAYCONTACT.INITIAL':'None',
            'DISPLAYCONTACT.PRINTAS':'Ashwin',
            'DISPLAYCONTACT.PHONE1':'None',
            'DISPLAYCONTACT.PHONE2':'None',
            'DISPLAYCONTACT.EMAIL1':'ashwin.t@fyle.in',
            'DISPLAYCONTACT.EMAIL2':'None',
            'VENDORACCOUNTNO':'None',
            'WHENMODIFIED':'03/03/2020 19:03:33',
            'VENDTYPE':'None',
            'ACCOUNTLABEL':'None',
            'APACCOUNT':'None',
            'APACCOUNTTITLE':'None',
            'STATUS':'active'
        }
    ],
    'post_vendors': {
        'data': {
            'vendor': {
                'RECORDNO':'51',
                'NAME':'Ashwin',
                'VENDORID':'Ashwin',
                'PARENTKEY':'None',
                'PARENTID':'None',
                'PARENTNAME':'None',
                'DISPLAYCONTACT.CONTACTNAME':'Ashwin(VAshwin)',
                'DISPLAYCONTACT.COMPANYNAME':'Ashwin',
                'DISPLAYCONTACT.FIRSTNAME':'FyleT',
                'DISPLAYCONTACT.LASTNAME':'FyleT',
                'DISPLAYCONTACT.INITIAL':'None',
                'DISPLAYCONTACT.PRINTAS':'Ashwin',
                'DISPLAYCONTACT.PHONE1':'None',
                'DISPLAYCONTACT.PHONE2':'None',
                'DISPLAYCONTACT.EMAIL1':'ashwin.t@fyle.in',
                'DISPLAYCONTACT.EMAIL2':'None',
                'VENDORACCOUNTNO':'None',
                'VENDTYPE':'None',
                'ACCOUNTLABEL':'None',
                'APACCOUNT':'None',
                'APACCOUNTTITLE':'None',
                'STATUS':'active'
            }
        }
    },
    'get_expense_types':[
        {
            'RECORDNO':'1',
            'ACCOUNTLABEL':'Airfare',
            'DESCRIPTION':'Airfare',
            'GLACCOUNTNO':'60200',
            'GLACCOUNTTITLE':'Travel',
            'STATUS':'active',
            'ITEMID':'1004'
        }
    ],
    'get_user_defined_dimensions': [{'objectName': 'DEPARTMENT', 'objectLabel': 'Department', 'termLabel': 'Department', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'LOCATION', 'objectLabel': 'Location', 'termLabel': 'Location', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'PROJECT', 'objectLabel': 'Project', 'termLabel': 'Project', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'CUSTOMER', 'objectLabel': 'Customer', 'termLabel': 'Customer', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'VENDOR', 'objectLabel': 'Vendor', 'termLabel': 'Vendor', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'EMPLOYEE', 'objectLabel': 'Employee', 'termLabel': 'Employee', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'ITEM', 'objectLabel': 'Item', 'termLabel': 'Item', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'CLASS', 'objectLabel': 'Class', 'termLabel': 'Class', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'CONTRACT', 'objectLabel': 'Contract', 'termLabel': 'Contract', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'TASK', 'objectLabel': 'Task', 'termLabel': 'Task', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'WAREHOUSE', 'objectLabel': 'Warehouse', 'termLabel': 'Warehouse', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}, {'objectName': 'COSTTYPE', 'objectLabel': 'Cost type', 'termLabel': 'Cost type', 'userDefinedDimension': 'false', 'enabledInGL': 'false'}, {'objectName': 'FIXEDASSET', 'objectLabel': 'Asset', 'termLabel': 'Asset', 'userDefinedDimension': 'false', 'enabledInGL': 'false'}, {'objectName': 'PLACE', 'objectLabel': 'Place', 'termLabel': 'Place', 'userDefinedDimension': 'true', 'enabledInGL': 'true'}, {'objectName': 'TEAM', 'objectLabel': 'Team', 'termLabel': 'Team', 'userDefinedDimension': 'true', 'enabledInGL': 'true'}],
    'get_dimension_value': [{'createdBy': '10', 'name': 'CCC', 'id': '10003', 'updatedBy': '10'}, {'createdBy': '10', 'name': 'Integrations', 'id': '10002', 'updatedBy': '10'}],
    'get_items': [{'RECORDNO': '59', 'ITEMID': '1011', 'STATUS': 'active', 'MRR': 'false', 'NAME': 'New item to be added', 'EXTENDED_DESCRIPTION': None, 'PRODUCTLINEID': None, 'GLGROUP': None, 'ITEMTYPE': 'Non-Inventory'}],
}
