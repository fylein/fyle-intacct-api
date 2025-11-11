import random
from datetime import datetime



today_date = datetime.now().strftime('%Y-%m-%d')
year = datetime.now().year
month = datetime.now().month
day = datetime.now().day
random_int = random.randint(1, 1000)


# REST payload for charge card transaction
REST_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD = {
  "txnDate": today_date,
  "creditCardAccount": {
    "id": "Mastercard - 6789"
  },
  "referenceNumber": f"E/{year}/{month}/T/{random_int}",
  "payee": "ABC Electric",
  "description": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
  "isInclusiveTax": False,
  "currency": {
    "baseCurrency": "USD",
    "txnCurrency": "USD"
  },
  "taxSolution": {
    'id': None,
    'key': None
  },
  "attachment": {
    "id": None,
    "key": None
  },
"lines": [
    {
      "glAccount": {
        "id": "1005"
      },
      "totalTxnAmount": "123.00",
      "txnAmount": "123.00",
      "dimensions": {
        "department": {
          "id": "001"
        },
        "location": {
          "id": "GC-DAL"
        },
        "project": {
          "id": "14"
        },
        "customer": {
          "id": None
        },
        "vendor": {
          "id": "V164"
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
      "description": f"owner@fyleforintegrationtests.in - 1005: Chase Checking - {today_date} - C/{year}/{month}/R/{random_int} - Testing CCC Export {random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txQaQgXrVx68&org_id=orjMvhugUguK",
      "taxEntries": [
        {
          "purchasingTaxDetail": {
            "key": None
          }
        }
      ],
      "isBillable": False,
      "isBilled": False
    }
  ]
}



# SOAP payload for charge card transaction  
SOAP_CHARGE_CARD_TRANSACTION_CREATE_PAYLOAD = {
    "chargecardid": "Mastercard - 6789",
    "paymentdate": {
        "year": year,
        "month": month,
        "day": day
    },
    "referenceno": f"E/{year}/{month}/T/{random_int}",
    "payee": "ABC Electric",
    "description": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
    "supdocid": None,
    "currency": "USD",
    "exchratetype": None,
    "inclusivetax": False,
    "ccpayitems": {
        "ccpayitem": [
            {
                "glaccountno": "1005",
                "description": f"owner@fyleforintegrationtests.in - 1005: Chase Checking - {today_date} - C/{year}/{month}/R/{random_int} - Testing CCC Export {random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txQaQgXrVx68&org_id=orjMvhugUguK",
                "paymentamount": 123.0,
                "departmentid": "001",
                "locationid": "GC-DAL",
                "customerid": None,
                "vendorid": "V164",
                "projectid": "14",
                "taskid": "78",
                "costtypeid": "EQ",
                "itemid": "CN014",
                "classid": "TestClassId",
                "customfields": {
                    "customfield": [
                        {
                            "customfieldname": "FYLE_EXPENSE_URL",
                            "customfieldvalue": "https://staging1.fyle.tech/app/admin/#/company_expenses?txnId=txQaQgXrVx68&org_id=orjMvhugUguK"
                        }
                    ]
                },
                "totaltrxamount": 123.0,
                "taxentries": {
                    "taxentry": {
                        "detailid": None
                    }
                },
                "billable": False
            }
        ]
    }
}

