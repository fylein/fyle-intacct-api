data = {
    "import_settings": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
            "import_code_fields": [],
        },
        "general_mappings": {
            "default_tax_code": {"name": "12.5% TR @12.5%", "id": "22"}
        },
        "mapping_settings": [
            {
                "source_field": "COST_CENTER",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "cost center",
            },
            {
                "source_field": "PROJECT",
                "destination_field": "CLASS",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "project",
            },
            {
                "source_field": "CLASS",
                "destination_field": "CUSTOMER",
                "import_to_fyle": True,
                "is_custom": True,
                "source_placeholder": "class",
            },
        ],
        "dependent_field_settings": {
            "cost_code_field_name": "Cost Code Jake Jellenahal",
            "cost_code_placeholder": "this is a dummy placeholder for cost code",
            "cost_type_field_name": "Cost Type Logan paul",
            "cost_type_placeholder": "this sia is dummy placeholder for cost type",
            "is_import_enabled": True,
        },
    },
    "import_settings_without_mapping": {
        "configurations": {
            "import_categories": True,
            "import_items": True,
            "charts_of_accounts": ["Expense"],
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
            "import_code_fields": [],
        },
        "general_mappings": {
            "default_tax_code": {"name": "12.5% TR @12.5%", "id": "22"}
        },
        "mapping_settings": [
            {
                "source_field": "CLASS",
                "destination_field": "CUSTOMER",
                "import_to_fyle": True,
                "is_custom": True,
                "source_placeholder": "class",
            }
        ],
        "dependent_field_settings": None,
    },
    "import_settings_schedule_check": {
        "configurations": {
            "import_categories": True,
            "import_items": True,
            "charts_of_accounts": ["Expense"],
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
        },
        "general_mappings": {
            "default_tax_code": {"name": "12.5% TR @12.5%", "id": "22"}
        },
        "mapping_settings": [
            {
                "source_field": "PROJECT",
                "destination_field": "PROJECT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "Select Project",
            }
        ],
        "dependent_field_settings": None,
    },
    "response": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
            "import_code_fields": []
        },
        "general_mappings": {
            "default_tax_code": {"name": "12.5% TR @12.5%", "id": "22"}
        },
        "mapping_settings": [
            {
                "source_field": "COST_CENTER",
                "destination_field": "CLASS",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "",
            },
            {
                "source_field": "PROJECT",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "",
            },
            {
                "source_field": "CLASS",
                "destination_field": "CUSTOMER",
                "import_to_fyle": True,
                "is_custom": True,
                "source_placeholder": "",
            },
        ],
        "workspace_id": 9,
        "dependent_field_settings": {
            "cost_code_field_name": "Cost Code Jake Jellenahal",
            "cost_code_placeholder": "this is a dummy placeholder for cost code",
            "cost_type_field_name": "Cost Type Logan paul",
            "cost_type_placeholder": "this sia is dummy placeholder for cost type",
            "is_import_enabled": True,
            "is_cost_type_import_enabled": True,
        },
    },
    "invalid_general_mappings": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
            "import_code_fields": [],
        },
        "general_mappings": {},
        "mapping_settings": [
            {
                "source_field": "COST_CENTER",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": "cost center",
            }
        ],
        "dependent_field_settings": None,
    },
    "invalid_mapping_settings": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
            "import_code_fields": [],
        },
        "general_mappings": {
            "default_tax_code": {"name": "12.5% TR @12.5%", "id": "22"}
        },
        "mapping_settings": None,
        "dependent_field_settings": None,
    },
    "import_setting_validation_payload": {
        "configurations": {
            "import_categories": False,
            "import_tax_codes": False,
            "import_vendors_as_merchants": False,
            "import_code_fields": [
                "PROJECT",
                "DEPARTMENT"
            ]
        },
        "general_mappings": {
            "default_tax_code": {
                "name": None,
                "id": None
            }
        },
        "mapping_settings": [
            {
                "source_field": "PROJECT",
                "destination_field": "PROJECT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": None
            },
            {
                "source_field": "COST_CENTER",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": None
            }
        ],
        "dependent_field_settings": None,
        "workspace_id": 1
    },
    "import_setting_validation_response": {
        "configurations": {
            "import_categories": False,
            "import_tax_codes": False,
            "import_vendors_as_merchants": False,
            "import_code_fields": [
                "PROJECT",
                "DEPARTMENT"
            ]
        },
        "general_mappings": {
            "default_tax_code": {
                "name": None,
                "id": None
            }
        },
        "mapping_settings": [
            {
                "source_field": "PROJECT",
                "destination_field": "PROJECT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": None
            },
            {
                "source_field": "COST_CENTER",
                "destination_field": "DEPARTMENT",
                "import_to_fyle": True,
                "is_custom": False,
                "source_placeholder": None
            }
        ],
        "dependent_field_settings": None,
        "workspace_id": 1
    }
}
