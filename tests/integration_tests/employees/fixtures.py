REST_CONTACT_CREATE_PAYLOAD = {
    'id': 'TEST_EMP_CONTACT_REST',
    'printAs': 'Test Employee Integration REST',
    'email1': 'testemployee@integration.test',
    'firstName': 'Test',
    'lastName': 'Employee REST'
}

SOAP_CONTACT_CREATE_PAYLOAD = {
    'CONTACTNAME': 'Test Employee Integration SOAP',
    'PRINTAS': 'Test Employee Integration SOAP',
    'EMAIL1': 'testemployee@integration.test',
    'FIRSTNAME': 'Test',
    'LASTNAME': 'Employee SOAP'
}

REST_EMPLOYEE_CREATE_PAYLOAD = {
    'id': 'TEST_EMP_REST',
    'primaryContact': {
        'id': 'TEST_EMP_CONTACT_REST'
    },
    'location': {
        'id': 'GC-DAL'
    },
    'department': {
        'id': '001'
    }
}

SOAP_EMPLOYEE_CREATE_PAYLOAD = {
    'EMPLOYEEID': 'TEST_EMP_SOAP',
    'PERSONALINFO': {
        'CONTACTNAME': 'Test Employee Integration SOAP'
    },
    'LOCATIONID': 'GC-DAL',
    'DEPARTMENTID': '001'
}
