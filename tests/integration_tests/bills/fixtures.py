import random
from datetime import datetime


today_date = datetime.now().strftime('%Y-%m-%d')
year = datetime.now().year
month = datetime.now().month
day = datetime.now().day

def get_random_string():
  return random.randbytes(6).hex()

def get_random_int():
  return random.randint(1, 100000)



def get_rest_bill_create_payload() -> dict:
  """
  Get REST bill create payload
  :return: REST bill create payload
  """
  return {
    "billNumber": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{get_random_int()}_{get_random_string()}_1",
    "vendor": {
      "id": "V100"
    },
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
        "allocation": {
          "id": None
        },
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
            "id": "C00010--Amazon"
          },
          "vendor": {
            "id": None
          },
          "employee": {
            "id": None
          },
          "item": {
            "id": "CN014"
          },
          "class": {
              "id": "TestClassId"
          },
          "task": {
            "id": "123"
          },
          "costType": {
            "id": "89"
          }
        },
        "memo": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{get_random_int()} -  - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txdhZD3g8mQL&org_id=orjMvhugUguK",
      }
    ]
  }



created_date = datetime.now().strftime('%m/%d/%Y')


# SOAP payload for bill  
def get_soap_bill_create_payload() -> dict:
  """
  Get SOAP bill create payload
  :return: SOAP bill create payload
  """
  return {
    "WHENCREATED": created_date,
    "VENDORID": "V100",
    "RECORDID": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{get_random_int()}_{get_random_string()}_2",
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
                "ENTRYDESCRIPTION": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{get_random_int()} -  - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txdhZD3g8mQL&org_id=orjMvhugUguK",
                "LOCATIONID": "GC-DAL",
                "DEPARTMENTID": "001",
                "PROJECTID": "12",
                "CUSTOMERID": "C00010--Amazon",
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
                }
            }
        ]
    }
}


# REST payload for bill
REST_BILL_CREATE_PAYLOAD_WITH_ALLOCATION = {
  "billNumber": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{get_random_int()}_{get_random_string()}_3",
  "vendor": {
    "id": "V100"
  },
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
      "allocation": {
        "id": "RENT"
      },
      "dimensions": {
        "location": {
          "id": None
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
          "id": None
        },
        "employee": {
          "id": None
        },
        "item": {
          "id": "CN014"
        },
        "class": {
            "id": "TestClassId"
        },
        "task": {
          "id": "123"
        },
        "costType": {
          "id": "89"
        },
        "nsp::udd_test": {
          "key": "10002"
        }
      },
      "memo": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{get_random_int()} -  - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txdhZD3g8mQL&org_id=orjMvhugUguK",
    }
  ]
}



created_date = datetime.now().strftime('%m/%d/%Y')

# SOAP payload for bill  
SOAP_BILL_CREATE_PAYLOAD_WITH_ALLOCATION = {
    "WHENCREATED": created_date,
    "VENDORID": "V100",
    "RECORDID": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{get_random_int()}_{get_random_string()}_4",
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
                "ENTRYDESCRIPTION": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{get_random_int()} -  - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txdhZD3g8mQL&org_id=orjMvhugUguK",
                "LOCATIONID": None,
                "DEPARTMENTID": "001",
                "PROJECTID": "12",
                "CUSTOMERID": None,
                "ITEMID": "CN014",
                "TASKID": "123",
                "COSTTYPEID": "89",
                "CLASSID": "TestClassId",
                "BILLABLE": False,
                "ALLOCATION": "RENT",
                "TAXENTRIES": {
                    "TAXENTRY": {
                        "DETAILID": None
                    }
                },
                "customfields": {
                    "customfield": [
                        {
                            "customfieldname": "GLDIMUDD_TEST",
                            "customfieldvalue": "10002"
                        }
                    ]
                }
            }
        ]
    }
}
