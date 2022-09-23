data = {
    'bill_payload': {
        'VendorRef': {
            'value': '43'
        },
        'APAccountRef': {
            'value': '33'
        },
        'DepartmentRef': {
            'value': 'None'
        },
        'TxnDate': '2022-01-21',
        'CurrencyRef': {
            'value': 'USD'
        },
        'PrivateNote': 'Reimbursable expense by ashwin.t@fyle.in on 2022-01-21 ',
        'Line': [
            {
                'Description': 'ashwin.t@fyle.in - Travel - 2022-01-21 - C/2022/01/R/8 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txlPjmNxssq1?org_id=orGcBCVPijjO',
                'DetailType': 'AccountBasedExpenseLineDetail',
                'Amount': 60.0,
                'AccountBasedExpenseLineDetail': {
                    'AccountRef': {
                        'value': '57'
                    },
                    'CustomerRef': {
                        'value': 'None'
                    },
                    'ClassRef': {
                        'value': 'None'
                    },
                    'TaxCodeRef': {
                        'value': 'None'
                    },
                    'TaxAmount': 0.0,
                    'BillableStatus': 'NotBillable'
                }
            }
        ]
    },
    'bank_transaction_payload': {
        'DocNumber': 'E/2022/01/T/9',
        'PaymentType': 'CreditCard',
        'AccountRef': {
            'value': '42'
        },
        'EntityRef': {
            'value': '58'
        },
        'DepartmentRef': {
            'value': 'None'
        },
        'TxnDate': '2022-01-21',
        'CurrencyRef': {
            'value': 'USD'
        },
        'PrivateNote': 'Credit card expense by ashwin.t@fyle.in on 2022-01-21 ',
        'Credit': False,
        'Line': [
            {
                'Description': 'ashwin.t@fyle.in - Travel - 2022-01-21 - C/2022/01/R/8 -  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txvh8qm7RTRI?org_id=orGcBCVPijjO',
                'DetailType': 'AccountBasedExpenseLineDetail',
                'Amount': 30.0,
                'AccountBasedExpenseLineDetail': {
                    'AccountRef': {
                        'value': '57'
                    },
                    'CustomerRef': {
                        'value': 'None'
                    },
                    'ClassRef': {
                        'value': 'None'
                    },
                    'TaxCodeRef': {
                        'value': 'None'
                    },
                    'TaxAmount': 0.0,
                    'BillableStatus': 'NotBillable'
                }
            }
        ]
    },
    'bill_response': {
        'DueDate': '2020-01-14',
        'Balance': 1000.0,
        'domain': 'QBO',
        'sparse': False,
        'Id': '146',
        'SyncToken': '0',
        'MetaData': {
            'CreateTime': '2020-01-14T02:18:29-08:00',
            'LastUpdatedTime': '2020-01-14T02:18:29-08:00'
        },
        'DocNumber': 'rphZKTDmSLU2',
        'TxnDate': '2020-01-14',
        'CurrencyRef': {
            'value': 'USD',
            'name': 'United States Dollar'
        },
        'PrivateNote': 'Report None / rphZKTDmSLU2 approved on 2020-01-14',
        'Line': [
            {
                'Id': '1',
                'LineNum': 1,
                'Description': 'Testing',
                'Amount': 1000.0,
                'DetailType': 'AccountBasedExpenseLineDetail',
                'AccountBasedExpenseLineDetail': {
                    'AccountRef': {
                        'value': '2',
                        'name': 'Retained Earnings'
                    },
                    'BillableStatus': 'NotBillable',
                    'TaxCodeRef': {
                        'value': 'NON'
                    }
                }
            }
        ],
        'VendorRef': {
            'value': '56',
            'name': 'Gokul'
        },
        'APAccountRef': {
            'value': '33',
            'name': 'Accounts Payable (A/P)'
        },
        'TotalAmt': 1000.0
    },
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
    'bill_object': {
        "Id": "21a31ed7-0a35-44d4-b4a1-64c0fdc65a1a",
        "Status": "OK",
        "ProviderName": "Fyle Staging",
        "DateTimeUTC": "/Date(1660833015693)/",
        "Invoices": [
            {
                "Type": "ACCPAY",
                "InvoiceID": "c35cf4b3-784a-408b-9ddf-df111dd2e073",
                "InvoiceNumber": "",
                "Reference": "2 - ashwin.t@fyle.in",
                "Prepayments": [

                ],
                "Overpayments":[

                ],
                "AmountDue":5.0,
                "AmountPaid":0.0,
                "SentToContact":False,
                "CurrencyRate":1.0,
                "IsDiscounted":False,
                "HasAttachments":False,
                "HasErrors":False,
                "Attachments":[

                ],
                "Contact":{
                    "ContactID": "9eecdd86-78bb-47c9-95df-986369748151",
                    "ContactStatus": "ACTIVE",
                    "Name": "Joanna",
                    "FirstName": "Joanna",
                    "LastName": "",
                    "EmailAddress": "ashwin.t@fyle.in",
                    "BankAccountDetails": "",
                    "Addresses": [
                        {
                            "AddressType": "STREET",
                            "City": "",
                            "Region": "",
                            "PostalCode": "",
                            "Country": ""
                        },
                        {
                            "AddressType": "POBOX",
                            "City": "",
                            "Region": "",
                            "PostalCode": "",
                            "Country": ""
                        }
                    ],
                    "Phones": [
                        {
                            "PhoneType": "DEFAULT",
                            "PhoneNumber": "",
                            "PhoneAreaCode": "",
                            "PhoneCountryCode": ""
                        },
                        {
                            "PhoneType": "DDI",
                            "PhoneNumber": "",
                            "PhoneAreaCode": "",
                            "PhoneCountryCode": ""
                        },
                        {
                            "PhoneType": "FAX",
                            "PhoneNumber": "",
                            "PhoneAreaCode": "",
                            "PhoneCountryCode": ""
                        },
                        {
                            "PhoneType": "MOBILE",
                            "PhoneNumber": "",
                            "PhoneAreaCode": "",
                            "PhoneCountryCode": ""
                        }
                    ],
                    "UpdatedDateUTC": "/Date(1659085778640+0000)/",
                    "ContactGroups": [

                    ],
                    "IsSupplier":True,
                    "IsCustomer":False,
                    "SalesTrackingCategories":[

                    ],
                    "PurchasesTrackingCategories":[

                    ],
                    "ContactPersons":[

                    ],
                    "HasValidationErrors":False
                },
                "DateString":"2022-08-02T00:00:00",
                "Date":"/Date(1659398400000+0000)/",
                "DueDateString":"2022-08-16T00:00:00",
                "DueDate":"/Date(1660608000000+0000)/",
                "Status":"PAID",
                "LineAmountTypes":"Exclusive",
                "LineItems":[
                    {
                        "Description": "ashwin.t@fyle.in, category - Food spent on 2020-05-25, report number - C/2022/05/R/16  - https://staging.fyle.tech/app/main/#/enterprise/view_expense/txUDvDmEV4ep?org_id=orPJvXuoLqvJ",
                        "UnitAmount": 4.62,
                        "TaxType": "INPUT",
                        "TaxAmount": 0.38,
                        "LineAmount": 4.62,
                        "AccountCode": "429",
                        "Tracking": [

                        ],
                        "Quantity":1.0,
                        "LineItemID":"51cca2e7-5bef-452c-83fb-2ca8c0865f37",
                        "ValidationErrors":[

                        ]
                    }
                ],
                "SubTotal":4.62,
                "TotalTax":0.38,
                "Total":5.0,
                "UpdatedDateUTC":"/Date(1659472064663+0000)/",
                "CurrencyCode":"USD"
            }
        ]
    },
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
    'get_projects': [{'RECORDNO': '111', 'PROJECTID': '10064', 'NAME': 'Direct Mail Campaign', 'DESCRIPTION': None, 'CURRENCY': 'AUD', 'PROJECTCATEGORY': 'Contract', 'PROJECTSTATUS': 'In Progress', 'PARENTKEY': None, 'PARENTID': None, 'PARENTNAME': None, 'STATUS': 'active', 'CUSTOMERKEY': '42', 'CUSTOMERID': '10064', 'CUSTOMERNAME': 'Med dot', 'PROJECTTYPE': 'AMP-Marketing', 'DEPARTMENTNAME': 'Services', 'LOCATIONID': '600', 'LOCATIONNAME': 'Australia', 'BUDGETID': None, 'MEGAENTITYID': '600', 'MEGAENTITYNAME': 'Australia'}],
    'get_departments': [{'RECORDNO': '3', 'DEPARTMENTID': '300', 'TITLE': 'Admin', 'PARENTKEY': None, 'PARENTID': None, 'SUPERVISORNAME': 'Tesla, Nikki', 'STATUS': 'active', 'CUSTTITLE': None}],
    'get_charge_card_accounts': [{'RECORDNO': '3', 'CARDID': 'Charge Card 1', 'DESCRIPTION': None, 'CARDTYPE': 'Visa', 'EXP_MONTH': 'January', 'EXP_YEAR': '2021', 'COMMCARD': 'C', 'STATUS': 'active', 'VENDORID': '20003', 'DEPT': None, 'LOCATION': None, 'LIABILITYTYPE': 'Credit', 'OUTSOURCECARD': None}],
    'get_classes':
    [{'NAME': 'Small Business', 'CLASSID': '400'}],
    'get_expense_payment_types':
    [{'RECORDNO': '1', 'NAME': 'Company Credit Card', 'DESCRIPTION': None, 'NONREIMBURSABLE': 'true', 'OFFSETACCTNO': None, 'OFFSETACCTTITLE': None, 'STATUS': 'active', 'WHENCREATED': '03/03/2020 20:27:09', 'WHENMODIFIED': '03/03/2020 20:27:09', 'CREATEDBY': '8', 'MODIFIEDBY': '8', 'MEGAENTITYKEY': None, 'MEGAENTITYID': None, 'MEGAENTITYNAME': None}],
    'get_location_entities':
    [{'RECORDNO': '9', 'LOCATIONID': '600', 'NAME': 'Australia', 'REPORTPRINTAS': None, 'SUPERVISORID': None, 'FIRSTMONTH': '1', 'FIRSTMONTHTAX': None, 'WEEKSTART': None, 'FEDERALID': '10-0000351', 'STARTDATE': None, 'ENDDATE': None, 'STATUS': 'active', 'HAS_IE_RELATION': 'false', 'CUSTOMERID': None, 'CUSTOMERNAME': None, 'VENDORID': None, 'VENDORNAME': None, 'CURRENCY': 'AUD', 'TAXID': '51976067581', 'ENABLELEGALCONTACT': 'false', 'LEGALNAME': None, 'LEGALADDRESS1': None, 'LEGALADDRESS2': None, 'LEGALCITY': None, 'LEGALSTATE': None, 'LEGALZIPCODE': None, 'LEGALCOUNTRY': None, 'OPCOUNTRY': 'Australia', 'ADDRESSCOUNTRYDEFAULT': 'Australia', 'RECORD_URL': 'https://www-p02.intacct.com/ia/acct/ur.phtml?.r=5jqUgbnTPWSyfcQt2WN8R_O-Kf-mmZi3S99kptb_bT0'}],
    'get_locations':
    [{'RECORDNO': '9', 'LOCATIONID': '600', 'NAME': 'Australia', 'PARENTID': None, 'STATUS': 'active', 'CURRENCY': 'AUD'}],
    'get_payment_accounts': [{'BANKACCOUNTID': '500_CHK', 'BANKACCOUNTNO': '525751035443', 'GLACCOUNTNO': '10050', 'BANKNAME': 'Demo Bank', 'ROUTINGNO': '121010303', 'BRANCHID': '101/1', 'BANKACCOUNTTYPE': 'checking', 'DEPARTMENTID': None, 'LOCATIONID': '500', 'STATUS': 'active', 'RECORDNO': '10', 'ACHBANKID': None, 'COMPANYNAME': None}],
    'get_tax_details': [{'RECORDNO': '78', 'DETAILID': 'UK Import Services Zero Rate', 'TAXUID': 'GB.EXInputServices_GB.ZeroGB.VAT', 'DESCRIPTION': 'UK Import Services Zero Rate', 'TAXTYPE': 'Purchase', 'VALUE': '0', 'MINTAXABLE': None, 'MAXTAXABLE': None, 'INCLUDE': None, 'MINTAX': None, 'MAXTAX': None, 'GLACCOUNT': '12620', 'TAXAUTHORITY': None, 'STATUS': 'active', 'REVERSECHARGE': 'false', 'TAXRATE': 'Zero', 'TAXSOLUTIONID': 'United Kingdom - VAT', 'MEGAENTITYKEY': None, 'MEGAENTITYID': None, 'MEGAENTITYNAME': None}],
    'get_dimensions':
    [{'objectName': 'DEPARTMENT', 'objectLabel': 'Department', 'termLabel': 'Department', 'userDefinedDimension': 'false', 'enabledInGL': 'true'}],
    'get_accounts': [{'RECORDNO': '287', 'ACCOUNTNO': '16200', 'TITLE': 'Patents & Licenses', 'ACCOUNTTYPE': 'balancesheet', 'NORMALBALANCE': 'debit', 'CLOSINGTYPE': 'non-closing account', 'STATUS': 'active', 'CATEGORY': 'Patents', 'ALTERNATIVEACCOUNT': 'None'}],
    'get_employees':
[{'RECORDNO': '6', 'EMPLOYEEID': '1005', 'SSN': '246602649', 'TITLE': 'Project Manager', 'LOCATIONID': None, 'DEPARTMENTID': '100', 'BIRTHDATE': '11/11/1982', 'STARTDATE': '08/17/2014', 'ENDDATE': None, 'STATUS': 'active', 'EMPLOYEETYPE': 'Full Time', 'EMPLOYEETYPE1099TYPE': None, 'GENDER': 'male', 'TERMINATIONTYPE': None, 'CONTACT.CONTACTNAME': 'Franco, Ryan', 'CONTACT.PREFIX': None, 'CONTACT.FIRSTNAME': 'Ryan', 'CONTACT.INITIAL': None, 'CONTACT.LASTNAME': 'Franco', 'CONTACT.COMPANYNAME': None, 'CONTACT.PRINTAS': 'Franco, Ryan', 'CONTACT.PHONE1': '415-468-5786', 'CONTACT.PHONE2': None, 'CONTACT.CELLPHONE': None, 'CONTACT.PAGER': None, 'CONTACT.FAX': None, 'CONTACT.EMAIL1': 'ryan@demo.com', 'CONTACT.EMAIL2': None, 'CONTACT.URL1': None, 'CONTACT.URL2': None, 'CONTACT.MAILADDRESS.ADDRESS1': '12401 Clinton Ave', 'CONTACT.MAILADDRESS.ADDRESS2': None, 'CONTACT.MAILADDRESS.CITY': 'NY', 'CONTACT.MAILADDRESS.STATE': 'NY', 'CONTACT.MAILADDRESS.ZIP': '10010', 'CONTACT.MAILADDRESS.COUNTRY': 'United States', 'CONTACT.MAILADDRESS.COUNTRYCODE': 'US', 'CURRENCY': None, 'WHENCREATED': '02/10/2020 19:57:41', 'WHENMODIFIED': '03/03/2020 19:03:33', 'PAYMETHODKEY': None, 'CONTACTKEY': '31', 'MEGAENTITYKEY': None, 'MEGAENTITYID': None, 'MEGAENTITYNAME': None}],
'get_customers': [{'NAME': 'AB SQUARE', 'CUSTOMERID': '10001'}],
'get_vendors': [{'RECORDNO': '51', 'NAME': 'Ashwin', 'VENDORID': 'Ashwin', 'PARENTKEY': None, 'PARENTID': None, 'PARENTNAME': None, 'DISPLAYCONTACT.CONTACTNAME': 'Ashwin(VAshwin)', 'DISPLAYCONTACT.COMPANYNAME': 'Ashwin', 'DISPLAYCONTACT.FIRSTNAME': 'FyleT', 'DISPLAYCONTACT.LASTNAME': 'FyleT', 'DISPLAYCONTACT.INITIAL': None, 'DISPLAYCONTACT.PRINTAS': 'Ashwin', 'DISPLAYCONTACT.PHONE1': None, 'DISPLAYCONTACT.PHONE2': None, 'DISPLAYCONTACT.EMAIL1': 'ashwin.t@fyle.in', 'DISPLAYCONTACT.EMAIL2': None, 'VENDORACCOUNTNO': None, 'VENDTYPE': None, 'ACCOUNTLABEL': None, 'APACCOUNT': None, 'APACCOUNTTITLE': None, 'STATUS': 'active'}],
'get_expense_types': [{'RECORDNO': '1', 'ACCOUNTLABEL': 'Airfare', 'DESCRIPTION': 'Airfare', 'GLACCOUNTNO': '60200', 'GLACCOUNTTITLE': 'Travel', 'STATUS': 'active', 'ITEMID': '1004'}],
}
