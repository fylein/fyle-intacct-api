data = {
    "import_settings": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
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
        "dependent_fields": {}
    },
    "import_settings_without_mapping": {
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
                "source_field": "CLASS",
                "destination_field": "CUSTOMER",
                "import_to_fyle": True,
                "is_custom": True,
                "source_placeholder": "class",
            }
        ],
        "dependent_fields": {}
    },
    "response": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
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
        "dependent_fields": {}
    },
    "invalid_general_mappings": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
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
        "dependent_fields": {}
    },
    "invalid_mapping_settings": {
        "configurations": {
            "import_categories": True,
            "import_tax_codes": True,
            "import_vendors_as_merchants": True,
        },
        "general_mappings": {
            "default_tax_code": {"name": "12.5% TR @12.5%", "id": "22"}
        },
        "mapping_settings": None,
        "dependent_fields": {}
    },
}
