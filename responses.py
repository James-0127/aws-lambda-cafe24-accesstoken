"""
This module provides helper functions to create HTTP responses.
"""

import json

def json_response(status_code: int, body_obj: dict):
    """
    Create a JSON HTTP response.
    """
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body_obj, default=str),
    }