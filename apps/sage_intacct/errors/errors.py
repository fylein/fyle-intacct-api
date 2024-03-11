errors_ref = {
    "EMPLOYEE": {
        "article_link" : None,
        "patterns" : [
            "The employee '([^']+)' is invalid."
        ]
    },
    "VENDOR": {
        "article_link" : None,
        "patterns" : [
            "The vendor '([^']+)' is invalid.",
            "Vendor '([^']+)' specified is not valid.",
            "The specified vendor '([^']+)' is not valid.",
            "Invalid Vendor '([^']+)' specified.",
            "Activate the vendor ([A-Z0-9-]+), then try again."
        ]
    },
    "CUSTOMER": {
        "article_link" : None,
        "patterns" : [
            "Customer '([^']+)' specified is not valid."
        ]
    },
    "JOB":{
        "article_link" : None,
        "patterns" : [
            "Job '([^']+)' specified is not valid.",
            "Invalid Job '([^']+)' specified."
        ]
    },
    "ACCOUNT": {
        "article_link" : None,
        "patterns" : [
            "The account number '([^']+)' requires a",
            "Account ([A-Z0-9-]+) is not valid",
            "This transaction is missing the Department dimension for the Account ([A-Z0-9-]+)",
            "This transaction is missing 'Department' dimension for the Account ([A-Z0-9-]+)",
            "This transaction is missing the Job dimension for the Account ([A-Z0-9-]+)",
            "This transaction is missing the Item dimension for the Account ([A-Z0-9-]+)",
            "This transaction is missing the Cost Code dimension for the Account ([A-Z0-9-]+).",
            "This transaction is missing the Location dimension for the Account ([A-Z0-9-]+)",
            "This transaction is missing the Grant dimension for the Account ([A-Z0-9-]+)",
            "This transaction is missing the Employee dimension for the Account ([A-Z0-9-]+)",
            "The specified GL account '([^']+)' : '([^']+)' is not valid. GL account is restricted by",
            "GL account '([^']+)': '([^']+)' specified is not valid. GL account is restricted",
            "The account number ([A-Z0-9-]+) is associated to the"
        ]
    },
    "DEPARTMENT": {
        "article_link" : None,
        "patterns" : [
            "Department '([^']+)': '([^']+)' specified is not valid. Department is restricted by GL account.",
            "Invalid Department ([A-Z0-9-]+) selected ",
            "Department must be ([^']+). This value is auto-filled",
            "The department '([^']+)' is invalid.",
            "Department ([^']+) is not valid"
        ]
    },
    "PROJECT": {
        "article_link" : None,
        "patterns" : [
            "The employee isn’t a resource of the project '([^']+)'.",
            "The Project '([^']+)' has a project status that prevents expense submittal.",
            "Project '([^']+)' specified is not valid.",
            "Invalid Project '([^']+)' specified.",
        ]
    },
    "LOCATION": {
        "article_link" : None,
        "patterns" : [
            "The location '([^']+)' is invalid.",
            "Location '([^']+)' is not valid",
            "Location must be ([A-Z0-9-]+). This value is auto-filled"
        ]
    },

}

