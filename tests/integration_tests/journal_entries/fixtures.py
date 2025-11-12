import random
from datetime import datetime


today_date = datetime.now().strftime('%Y-%m-%d')
year = datetime.now().year
month = datetime.now().month
day = datetime.now().day
random_int = random.randint(1, 1000)


# REST payload for journal entry
REST_JOURNAL_ENTRY_CREATE_PAYLOAD = {
  "glJournal": {
    "id": "FYLE_JE"
  },
  "postingDate": today_date,
  "description": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
  "lines": [
    {
      "txnType": "credit",
      "txnAmount": "123.00",
      "isBillable": False,
      "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
      "glAccount": {
        "id": "2000"
      },
      "allocation": {
        "id": None
      },
      "dimensions": {
        "department": {
          "id": "001"
        },
        "location": {
          "id": "RES002"
        },
        "project": {
          "id": "12"
        },
        "customer": {
          "id": "C00010--Amazon"
        },
        "vendor": {
          "id": "V104"
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
      }
    },
    {
      "txnType": "debit",
      "txnAmount": "123.00",
      "isBillable": False,
      "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
      "glAccount": {
        "id": "1900"
      },
      "allocation": {
        "id": None
      },
      "dimensions": {
        "department": {
          "id": "001"
        },
        "location": {
          "id": "RES002"
        },
        "project": {
          "id": "12"
        },
        "customer": {
          "id": "C00010--Amazon"
        },
        "vendor": {
          "id": "V104"
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
      }
    }
  ]
}


created_date = datetime.now().strftime('%m/%d/%Y')

# SOAP payload for journal entry  
SOAP_JOURNAL_ENTRY_CREATE_PAYLOAD = {
    "recordno": None,
    "journal": "FYLE_JE",
    "batch_date": today_date,
    "batch_title": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
    "supdocid": None,
    "entries": [
        {
            "glentry": [
                {
                    "currency": "USD",
                    "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
                    "department": "001",
                    "location": "RES002",
                    "projectid": "12",
                    "customerid": "C00010--Amazon",
                    "vendorid": "V104",
                    "employeeid": None,
                    "classid": "TestClassId",
                    "itemid": "CN014",
                    "taskid": "123",
                    "costtypeid": "89",
                    "allocation": None,
                    "accountno": "2000",
                    "amount": 123.0,
                    "tr_type": -1,
                    "billable": None
                },
                {
                    "currency": "USD",
                    "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
                    "department": "001",
                    "location": "RES002",
                    "projectid": "12",
                    "customerid": "C00010--Amazon",
                    "vendorid": "V104",
                    "employeeid": None,
                    "classid": "TestClassId",
                    "itemid": "CN014",
                    "taskid": "123",
                    "costtypeid": "89",
                    "allocation": None,
                    "accountno": "1900",
                    "amount": 123.0,
                    "tr_type": 1,
                    "billable": False,
                    "taxentries": {
                        "taxentry": {
                            "trx_tax": None,
                            "detailid": None
                        }
                    }
                }
            ]
        }
    ]
}




# REST payload for journal entry
REST_JOURNAL_ENTRY_CREATE_PAYLOAD_WITH_ALLOCATION = {
  "glJournal": {
    "id": "FYLE_JE"
  },
  "postingDate": today_date,
  "description": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
  "lines": [
    {
      "txnType": "credit",
      "txnAmount": "123.00",
      "isBillable": False,
      "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
      "glAccount": {
        "id": "2000"
      },
      "allocation": {
        "id": "RENT"
      },
      "dimensions": {
        "department": {
          "id": "001"
        },
        "location": {
          "id": None
        },
        "project": {
          "id": "12"
        },
        "customer": {
          "id": None
        },
        "vendor": {
          "id": "V104"
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
      }
    },
    {
      "txnType": "debit",
      "txnAmount": "123.00",
      "isBillable": False,
      "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
      "glAccount": {
        "id": "1900"
      },
      "allocation": {
        "id": "RENT"
      },
      "dimensions": {
        "department": {
          "id": "001"
        },
        "location": {
          "id": None
        },
        "project": {
          "id": "12"
        },
        "customer": {
          "id": None
        },
        "vendor": {
          "id": "V104"
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
      }
    }
  ]
}


created_date = datetime.now().strftime('%m/%d/%Y')

# SOAP payload for journal entry  
SOAP_JOURNAL_ENTRY_CREATE_PAYLOAD_WITH_ALLOCATION = {
    "recordno": None,
    "journal": "FYLE_JE",
    "batch_date": today_date,
    "batch_title": f"owner@fyleforintegrationtests.in - Hrishabh T - E/{year}/{month}/T/{random_int}",
    "supdocid": None,
    "entries": [
        {
            "glentry": [
                {
                    "currency": "USD",
                    "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
                    "department": "001",
                    "location": None,
                    "projectid": "12",
                    "customerid": None,
                    "vendorid": "V104",
                    "employeeid": None,
                    "classid": "TestClassId",
                    "itemid": "CN014",
                    "taskid": "123",
                    "costtypeid": "89",
                    "allocation": "RENT",
                    "accountno": "2000",
                    "amount": 123.0,
                    "tr_type": -1,
                    "billable": None,
                    "customfields": {
                        "customfield": [
                            {
                                "customfieldname": "GLDIMUDD_TEST",
                                "customfieldvalue": "10002"
                            }
                        ]
                    }
                },
                {
                    "currency": "USD",
                    "description": f"owner@fyleforintegrationtests.in - 1900: Goodwill - {today_date} - C/{year}/{month}/R/{random_int} - https://staging.fyle.tech/app/admin/#/company_expenses?txnId=txyacPycOcqE&org_id=orjMvhugUguK",
                    "department": "001",
                    "location": None,
                    "projectid": "12",
                    "customerid": None,
                    "vendorid": "V104",
                    "employeeid": None,
                    "classid": "TestClassId",
                    "itemid": "CN014",
                    "taskid": "123",
                    "costtypeid": "89",
                    "allocation": "RENT",
                    "accountno": "1900",
                    "amount": 123.0,
                    "tr_type": 1,
                    "billable": False,
                    "taxentries": {
                        "taxentry": {
                            "trx_tax": None,
                            "detailid": None
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
    ]
}