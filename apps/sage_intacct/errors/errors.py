from django.conf import settings


errors_ref = {
    "EMPLOYEE": {
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317015-employee-related-sage-intacct-errors',
        "patterns": [
            "The employee '([^']+)' is invalid."
        ]
    },
    "VENDOR": {
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317003-vendor-related-sage-intacct-errors',
        "patterns": [
            "The vendor '([^']+)' is invalid.",
            "Vendor '([^']+)' specified is not valid.",
            "The specified vendor '([^']+)' is not valid.",
            "Invalid Vendor '([^']+)' specified.",
            "Activate the vendor ([A-Z0-9-]+), then try again."
        ]
    },
    "CUSTOMER": {
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317011-customer-related-sage-intacct-errors',
        "patterns": [
            "Customer '([^']+)' specified is not valid."
        ]
    },
    "JOB":{
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317014-job-related-sage-intacct-errors',
        "patterns": [
            "Job '([^']+)' specified is not valid.",
            "Invalid Job '([^']+)' specified."
        ]
    },
    "ACCOUNT": {
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317035-account-related-sage-intacct-errors',
        "patterns": [
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
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317032-department-related-sage-intacct-errors',
        "patterns": [
            "Department '([^']+)': '([^']+)' specified is not valid. Department is restricted by GL account.",
            "Invalid Department ([A-Z0-9-]+) selected ",
            "Department must be ([^']+). This value is auto-filled",
            "The department '([^']+)' is invalid.",
            "Department ([^']+) is not valid"
        ]
    },
    "PROJECT": {
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317068-project-related-sage-intacct-errors',
        "patterns": [
            "The employee isn’t a resource of the project '([^']+)'.",
            "The Project '([^']+)' has a project status that prevents expense submittal.",
            "Project '([^']+)' specified is not valid.",
            "Invalid Project '([^']+)' specified.",
        ]
    },
    "LOCATION": {
        "article_link": settings.HELP_ARTICLE_DOMAIN + '/en/articles/9317021-location-related-sage-intacct-errors',
        "patterns": [
            "The location '([^']+)' is invalid.",
            "Location '([^']+)' is not valid",
            "Location must be ([A-Z0-9-]+). This value is auto-filled"
        ]
    },
}
