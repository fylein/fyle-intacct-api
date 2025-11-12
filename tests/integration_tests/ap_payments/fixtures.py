import random
from datetime import datetime


today_date = datetime.now().strftime('%Y-%m-%d')
year = datetime.now().year
month = datetime.now().month
day = datetime.now().day
random_int = random.randint(1, 1000)

def get_rest_ap_payment_create_payload(id: str) -> dict:
  """
  Get REST AP Payment create payload
  :param id: ID
  :return: REST AP Payment create payload
  """
  return {
		"financialEntity": {
			"id": "TCG WF Checking"
		},
		"paymentDate": today_date,
		"description": f"Payment for Bill - C/{year}/{month}/R/{random_int}",
		"baseCurrency": {
			"currency": "USD"
		},
		"txnCurrency": {
			"currency": "USD"
		},
		"paymentMethod": "Cash",
		"vendor": {
			"id": "V104"
		},
		"details": [
			{
				"txnCurrency": {
					"paymentAmount": "126.00"
				},
				"bill": {
					"id": id
				}
			}
		]
	}




def get_soap_ap_payment_create_payload(record_key: str) -> dict:
  """
  Get SOAP AP Payment create payload
  :param record_key: Record key
  :return: SOAP AP Payment create payload
  """
  payment_date = datetime.now().strftime('%m/%d/%Y')

  return {
	"FINANCIALENTITY": "TCG WF Checking",
	"PAYMENTMETHOD": "Cash",
	"VENDORID": "V104",
	"DESCRIPTION": f"Payment for Bill - C/{year}/{month}/R/{random_int}",
	"PAYMENTDATE": payment_date,
	"CURRENCY": "USD",
	"BASECURR": "USD",
	"APPYMTDETAILS": {
		"APPYMTDETAIL": [{
			"RECORDKEY": record_key,
			"TRX_PAYMENTAMOUNT": 126.0
		}]
	}
}
