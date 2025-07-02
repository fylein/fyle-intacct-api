data = {
    'e2e_setup_payload': {
        'workspace_id': 2,
    },
    'e2e_setup_invalid_workspace_id_payload': {
        'workspace_id': 0,  # Invalid workspace ID (should be > 0)
    },
    'e2e_destroy_payload': {
        'org_id': 'test_org_123'
    },
    'e2e_destroy_empty_org_id_payload': {
        'org_id': ''  # Empty org_id
    },
    'e2e_destroy_nonexistent_payload': {
        'org_id': 'nonexistent_org'
    }
}
