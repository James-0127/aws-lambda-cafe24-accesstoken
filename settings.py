"""
This module reads configuration from environment variables.
"""
import os

def get_pg_config():
    """
    Returns Postgres connection configuration from environment variables.
    """
    return {
        "host": os.environ.get("PGHOST"),
        "port": os.environ.get("PGPORT", "5432"),
        "user": os.environ.get("PGUSER"),
        "password": os.environ.get("PGPASSWORD"),
        "database": os.environ.get("PGDATABASE"),
    }

def get_expected_state_secret():
    """
    OAuth state 검증에 사용 (콜백 핸들러용)
    """
    return os.environ.get("EXPECTED_STATE_SECRET")

def get_cafe24_config():
    """
    Returns Cafe24 OAuth configuration from environment variables.
    """
    return {
        "mall_id": os.environ.get("CAFE24_MALL_ID"),
        "client_id": os.environ.get("CAFE24_CLIENT_ID"),
        "client_secret": os.environ.get("CAFE24_CLIENT_SECRET"),
        "redirect_uri": os.environ.get("CAFE24_REDIRECT_URI"),
    }