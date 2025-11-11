import random
from datetime import datetime



today_date = datetime.now().strftime('%Y-%m-%d')
year = datetime.now().year
month = datetime.now().month
day = datetime.now().day
random_int = random.randint(1, 1000)


# REST payload for bill
REST_BILL_CREATE_PAYLOAD = {
  "billNumber": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}_1",
  "vendor": {
    "id": "V100"
  },
  "referenceNumber": f"E/{year}/{month}/T/{random_int}",
  "description": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
  "createdDate": today_date,
  "postingDate": today_date,
  "dueDate": today_date,
  "currency": {
    "baseCurrency": "USD",
    "txnCurrency": "USD",
  },
  "attachment": {
    "id": None,
    "key": None
  },
  "isTaxInclusive": False,
  "lines": [
    {
      "glAccount": {
        "id": "1900"
      },
      "txnAmount": "123.00",
      "totalTxnAmount": "123.00",
      "dimensions": {
        "location": {
          "id": "GC-DAL"
        },
        "department": {
          "id": "001"
        },
        "project": {
          "id": "12"
        },
        "customer": {
          "id": None
        },
        "vendor": {
          "id": "V100"
        },
        "employee": {
          "id": None
        },
        "item": {
          "id": "CN014"
        },
        "class": {
            "id": "TestClassId"
        }
      },
      "memo": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} -  - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txdhZD3g8mQL&org_id=orjMvhugUguK",
    }
  ]
}



created_date = datetime.now().strftime('%m/%d/%Y')

# SOAP payload for bill  
SOAP_BILL_CREATE_PAYLOAD = {
    "WHENCREATED": created_date,
    "VENDORID": "V100",
    "RECORDID": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}_2",
    "WHENDUE": created_date,
    "BASECURR": "USD",
    "SUPDOCID": None,
    "CURRENCY": "USD",
    "EXCH_RATE_TYPE_ID": None,
    "APBILLITEMS": {
        "APBILLITEM": [
            {
                "ACCOUNTNO": "1900",
                "TRX_AMOUNT": 123.0,
                "TOTALTRXAMOUNT": 123.0,
                "ENTRYDESCRIPTION": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} -  - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txdhZD3g8mQL&org_id=orjMvhugUguK",
                "LOCATIONID": "GC-DAL",
                "DEPARTMENTID": "001",
                "PROJECTID": "12",
                "CUSTOMERID": None,
                "ITEMID": "CN014",
                "TASKID": "123",
                "COSTTYPEID": "89",
                "CLASSID": "TestClassId",
                "BILLABLE": False,
                "ALLOCATION": None,
                "TAXENTRIES": {
                    "TAXENTRY": {
                        "DETAILID": None
                    }
                },
                "customfields": {
                    "customfield": [
                        {
                            "customfieldname": "FYLE_EXPENSE_URL",
                            "customfieldvalue": "https://staging1.fyle.tech/app/admin/#/company_expenses?txnId=txdhZD3g8mQL&org_id=orjMvhugUguK"
                        }
                    ]
                }
            }
        ]
    }
}
