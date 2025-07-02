import json
import os
from typing import Optional

import requests
from django.conf import settings
from django.db import migrations
from django.db.utils import ProgrammingError

from apps.fyle.helpers import get_access_token


def safe_run_sql(sql_files: list) -> list:
    """
    Safely create migrations.RunSQL operations from a list of SQL file paths.
    Handles FileNotFoundError for missing files and lets ProgrammingError surface naturally.
    """
    operations = []
    for file_path in sql_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as sql_file:
                sql = sql_file.read()
            operations.append(migrations.RunSQL(sql=sql, reverse_sql=None))
        except ProgrammingError as pe:
            raise ProgrammingError(
                f"SQL syntax error in file {file_path}: {pe}"
            ) from pe
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error in file {file_path}: {e}"
            ) from e

    return operations


def is_safe_environment() -> bool:
    """Check if we're in a safe environment for E2E operations"""
    return getattr(settings, 'ALLOW_E2E_SETUP', False)


def delete_request(url: str, body: dict, refresh_token: Optional[str] = None) -> Optional[dict]:
    """
    Create a HTTP delete request.
    """
    access_token = None
    api_headers = {
        'Content-Type': 'application/json',
    }
    if refresh_token:
        access_token = get_access_token(refresh_token)

        api_headers['Authorization'] = 'Bearer {0}'.format(access_token)

    response = requests.delete(
        url,
        headers=api_headers,
        data=json.dumps(body)
    )

    if response.status_code in [200, 201, 204]:
        if response.text:
            return json.loads(response.text)
        return None
    else:
        raise Exception(response.text)
