data = {
    'e2e_setup_payload': {
        'workspace_id': 2,
    },
    'e2e_setup_invalid_workspace_id_payload': {
        'workspace_id': 0,  # Invalid workspace ID (should be > 0)
    },
    'e2e_destroy_payload': {
        'workspace_id': 2,
    },
    'e2e_destroy_empty_payload': {},
    'e2e_destroy_nonexistent_payload': {
        'workspace_id': 234823,
    }
}
