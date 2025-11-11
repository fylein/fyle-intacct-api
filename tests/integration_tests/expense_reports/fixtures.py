import random
from datetime import datetime


today_date = datetime.now().strftime('%Y-%m-%d')
year = datetime.now().year
month = datetime.now().month
day = datetime.now().day
random_int = random.randint(1, 1000)


# REST payload for expense report
REST_EXPENSE_REPORT_CREATE_PAYLOAD = {
  "state": "submitted",
  "expenseReportNumber": f"E/{year}/{month}/T/{random_int}",
  "employee": {
    "id": "Chris Curtis"
  },
  "createdDate": today_date,
  "basePayment": {
    "baseCurrency": "USD"
  },
  "reimbursement": {
    "reimbursementCurrency": "USD"
  },
  "description": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
  "lines": [
    {
      "expenseType": {
        "id": "Elon Baba"
      },
      "txnCurrency": "USD",
      "txnAmount": "123.0",
      "entryDate": today_date,
      "paymentType": {
        "id": "Elon Baba CCC"
      },
      "paidTo": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txRZmAk6Jz3i&org_id=orjMvhugUguK",
      "dimensions": {
        "location": {
          "id": "RES002"
        },
        "department": {
          "id": "001"
        },
        "class": {
          "id": "TestClassId"
        },
        "item": {
          "id": "CN014"
        },
        "employee": {
          "id": "Chris Curtis"
        },
        "vendor": {
          "id": "V104"
        },
        "customer": {
          "id": None
        },
        "project": {
          "id": "12"
        },
        "task": {
          "id": "123"
        }
      }
    }
  ]
}


created_date = datetime.now().strftime('%m/%d/%Y')

# SOAP payload for expense report  
SOAP_EXPENSE_REPORT_CREATE_PAYLOAD = {
    "employeeid": "Chris Curtis",
    "datecreated": {
        "year": year,
        "month": month,
        "day": day
    },
    "state": "Submitted",
    "supdocid": None,
    "description": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
    "basecurr": "USD",
    "currency": "USD",
    "expenses": {
        "expense": [
            {
                "expensetype": "Elon Baba",
                "amount": 123.0,
                "expensedate": {
                    "year": year,
                    "month": month,
                    "day": day
                },
                "memo": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txRZmAk6Jz3i&org_id=orjMvhugUguK",
                "locationid": "RES002",
                "departmentid": "001",
                "customfields": {
                    "customfield": [
                        {
                            "customfieldname": "FYLE_EXPENSE_URL",
                            "customfieldvalue": "https://staging1.fyle.tech/app/admin/#/company_expenses?txnId=txRZmAk6Jz3i&org_id=orjMvhugUguK"
                        }
                    ]
                },
                "projectid": "12",
                "taskid": "123",
                "costtypeid": "89",
                "customerid": None,
                "itemid": "CN014",
                "classid": "TestClassId",
                "billable": False,
                "exppmttype": "Elon Baba CCC",
                "totaltrxamount": 123.0,
                "taxentries": {
                    "taxentry": {
                        "detailid": None
                    }
                }
            }
        ]
    }
}