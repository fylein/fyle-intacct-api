import random


random_string = random.randbytes(5).hex()


# REST payload for attachment
REST_ATTACHMENT_CREATE_PAYLOAD = {
  "id": f"Random-{random_string}-1",
  "name": "Random 123 - 1",
  "folder": {
    "id": "FyleAttachments"
  },
  "files": [
    {
      "name": "Random 123 - 1.png",
      "data": "aGVsbG8gd29ybGQhIHRoaXMgaXMgYmFzZTY0IGVuY29kZWQgZGF0YQ=="
    }
  ]
}



# SOAP payload for attachment  
SOAP_ATTACHMENT_CREATE_PAYLOAD = {
    'supdocid': f'Random-{random_string}-2',
    'supdocfoldername': 'FyleAttachments',
    'attachments': {
        'attachment': [{
          'attachmentname': "Random 123 - 1",
            'attachmenttype': 'png',
            'attachmentdata': "aGVsbG8gd29ybGQhIHRoaXMgaXMgYmFzZTY0IGVuY29kZWQgZGF0YQ==",
        }]
    }
}
