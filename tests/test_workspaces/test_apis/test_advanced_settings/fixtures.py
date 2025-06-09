data = {
    "advanced_settings": {
        "configurations": {
            "change_accounting_period": True,
            "sync_fyle_to_sage_intacct_payments": True,
            "sync_sage_intacct_to_fyle_payments": False,
            "auto_create_destination_entity": False,
            "memo_structure": ["merchant", "purpose"],
            "auto_create_merchants_as_vendors": False,
            "je_single_credit_line": False,
        },
        "general_mappings": {
            "payment_account": {"id": "100", "name": "First Community Bank"},
            "default_location": {"id": "100", "name": "Headquarters"},
            "default_department": {"id": "100", "name": "Sales"},
            "default_class": {"id": "100", "name": "Sales"},
            "default_project": {"id": "100", "name": "Sales"},
            "default_item": {"id": "100", "name": "Sales"},
            "use_intacct_employee_departments": True,
            "use_intacct_employee_locations": True,
        },
        "workspace_schedules": {
            "enabled": True,
            "interval_hours": 24,
            "emails_selected": ["fyle@fyle.in"],
            "additional_email_options": {},
            "is_real_time_export_enabled": False
        },
    },
    "response": {
        "configurations": {
            "change_accounting_period": True,
            "sync_fyle_to_sage_intacct_payments": True,
            "sync_sage_intacct_to_fyle_payments": False,
            "auto_create_destination_entity": False,
            "memo_structure": ["merchant", "purpose"],
            "auto_create_merchants_as_vendors": False,
            "je_single_credit_line": False,
        },
        "general_mappings": {
            "payment_account": {"id": "100", "name": "First Community Bank"},
            "default_location": {"id": "100", "name": "Headquarters"},
            "default_department": {"id": "100", "name": "Sales"},
            "default_class": {"id": "100", "name": "Sales"},
            "default_project": {"id": "100", "name": "Sales"},
            "default_item": {"id": "100", "name": "Sales"},
            "use_intacct_employee_departments": True,
            "use_intacct_employee_locations": True,
        },
        "workspace_schedules": {
            "enabled": True,
            "start_datetime": "now()",
            "interval_hours": 24,
            "emails_selected": [],
            "additional_email_options": [],
            "is_real_time_export_enabled": False
        },
        "workspace_id": 9,
    },
    "validate": {
        "workspace_general_settings": {},
        "general_mappings": {},
        "workspace_schedules": {},
    },
}
