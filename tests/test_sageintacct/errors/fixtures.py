error_msgs = [
        # Employee Errors
        "The employee '1005' is invalid.",
        # Account Errors
        "The account number '16200' requires a",
        "Account 16200 is not valid",
        "This transaction is missing the Department dimension for the Account 16200",
        "This transaction is missing 'Department' dimension for the Account 16200",
        "This transaction is missing the Job dimension for the Account 16200",
        "This transaction is missing the Item dimension for the Account 16200",
        "This transaction is missing the Cost Code dimension for the Account 16200.",
        "This transaction is missing the Location dimension for the Account 16200",
        "This transaction is missing the Grant dimension for the Account 16200",
        "This transaction is missing the Employee dimension for the Account 16200",
        "The specified GL account '16200' : '16200' is not valid. GL account is restricted by",
        "GL account '16200': '16200' specified is not valid. GL account is restricted",
        "The account number 16200 is associated to the",
        # Department Errors
        "Department '300': '300' specified is not valid. Department is restricted by GL account.",
        "Invalid Department 300 selected ",
        "Department must be 300. This value is auto-filled",
        "The department '300' is invalid.",
        "Department 300 is not valid",
        # Vendor Errors
        "The vendor 'Vaishnavi Primary' is invalid.",
        "Vendor 'Vaishnavi Primary' specified is not valid.",
        "The specified vendor 'Vaishnavi Primary' is not valid.",
        "Invalid Vendor 'Vaishnavi Primary' specified.",
        "Activate the vendor VM, then try again.",
        # Customer Errors
        "Customer '10001' specified is not valid.",
        # Project Errors
        "The employee isn’t a resource of the project '10064'.",
        "The Project '10064' has a project status that prevents expense submittal.",
        "Project '10064' specified is not valid.",
        "Invalid Project '10064' specified.",
        # Location Errors
        "The location '600' is invalid.",
        "Location '600' is not valid",
        "Location must be 600. This value is auto-filled"
    ]

result_dict_list = [
        {"attribute_type": "EMPLOYEE", "destination_id": "1005", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "DEPARTMENT", "destination_id": "300", "article_link" : None},
        {"attribute_type": "DEPARTMENT", "destination_id": "300", "article_link" : None},
        {"attribute_type": "DEPARTMENT", "destination_id": "300", "article_link" : None},
        {"attribute_type": "DEPARTMENT", "destination_id": "300", "article_link" : None},
        {"attribute_type": "DEPARTMENT", "destination_id": "300", "article_link" : None},
        {"attribute_type": "VENDOR", "destination_id": "Vaishnavi Primary", "article_link" : None},
        {"attribute_type": "VENDOR", "destination_id": "Vaishnavi Primary", "article_link" : None},
        {"attribute_type": "VENDOR", "destination_id": "Vaishnavi Primary", "article_link" : None},
        {"attribute_type": "VENDOR", "destination_id": "Vaishnavi Primary", "article_link" : None},
        {"attribute_type": "VENDOR", "destination_id": "VM", "article_link" : None},
        {"attribute_type": "CUSTOMER", "destination_id": "10001", "article_link" : None},
        {"attribute_type": "PROJECT", "destination_id": "10064", "article_link" : None},
        {"attribute_type": "PROJECT", "destination_id": "10064", "article_link" : None},
        {"attribute_type": "PROJECT", "destination_id": "10064", "article_link" : None},
        {"attribute_type": "PROJECT", "destination_id": "10064", "article_link" : None},
        {"attribute_type": "LOCATION", "destination_id": "600", "article_link" : None},
        {"attribute_type": "LOCATION", "destination_id": "600", "article_link" : None},
        {"attribute_type": "LOCATION", "destination_id": "600", "article_link" : None}
    ]

error_dict = [
        {"attribute_type": "EMPLOYEE", "destination_id": "1005", "article_link" : None},
        {"attribute_type": "ACCOUNT", "destination_id": "16200", "article_link" : None},
        {"attribute_type": "DEPARTMENT", "destination_id": "300", "article_link" : None},
        {"attribute_type": "VENDOR", "destination_id": "Vaishnavi Primary", "article_link" : None},
        {"attribute_type": "CUSTOMER", "destination_id": "10001", "article_link" : None},
        {"attribute_type": "PROJECT", "destination_id": "10064", "article_link" : None},
        {"attribute_type": "LOCATION", "destination_id": "600", "article_link" : None}
    ]

entity_result_dict_list = [
    {'destination_id': '1005', 'value': 'Franco, Ryan'},
    {'destination_id': '16200', 'value': 'Patents & Licenses'},
    {'destination_id': '300', 'value': 'Admin'},
    {'destination_id': 'Vaishnavi Primary', 'value': 'Vaishnavi Primary'},
    {'destination_id': '10001', 'value': 'AB SQUARE'},
    {'destination_id': '10064', 'value': 'Direct Mail Campaign'},
    {'destination_id': '600', 'value': 'Australia'}
]

input_strings = [
        "The employee '1005' is invalid.",
        "The account number '16200' requires a",
        "Department '300': '300' specified is not valid. Department is restricted by GL account.",
        "This transaction is missing the Department dimension for the Account 16200",
        "The specified GL account '16200' : '16200' is not valid. GL account is restricted by",
        "Department must be 300. This value is auto-filled",
        "The department '300' is invalid.",
        "Department 300 is not valid",
        "The vendor 'Vaishnavi Primary' is invalid.",
        "Vendor 'Vaishnavi Primary' specified is not valid.",
        "Customer '10001' specified is not valid.",
        "The employee isn’t a resource of the project '10064'.",
        "The Project '10064' has a project status that prevents expense submittal.",
        "The location '600' is invalid.",
        "Location '600' is not valid",
        "Location must be 600. This value is auto-filled"
    ]

replacements = [
    {'destination_id': '1005', 'value': 'Franco, Ryan'},
    {'destination_id': '16200', 'value': 'Patents & Licenses'},
    {'destination_id': '300', 'value': 'Admin'},
    {'destination_id': '16200', 'value': 'Patents & Licenses'},
    {'destination_id': '16200', 'value': 'Patents & Licenses'},
    {'destination_id': '300', 'value': 'Admin'},
    {'destination_id': '300', 'value': 'Admin'},
    {'destination_id': '300', 'value': 'Admin'},
    {'destination_id': 'Vaishnavi Primary', 'value': 'Vaishnavi Primary'},
    {'destination_id': 'Vaishnavi Primary', 'value': 'Vaishnavi Primary'},
    {'destination_id': '10001', 'value': 'AB SQUARE'},
    {'destination_id': '10064', 'value': 'Direct Mail Campaign'},
    {'destination_id': '10064', 'value': 'Direct Mail Campaign'},
    {'destination_id': '600', 'value': 'Australia'},
    {'destination_id': '600', 'value': 'Australia'},
    {'destination_id': '600', 'value': 'Australia'}
]
