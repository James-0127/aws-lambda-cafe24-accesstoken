"""
This module provides functions to store and update Cafe24 OAuth tokens in the database.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict
from settings import get_cafe24_config
from db import execute_upsert_token, now_utc

KST = timezone(timedelta(hours=9))

def _parse_iso8601_as_utc(ts_str: str | None) -> datetime:
    """
    Cafe24가 주는 '2018-11-07T20:12:25.916' 같은 문자열을
    tz-aware UTC datetime으로 변환.
    """
    if ts_str is None:
        return now_utc()
    dt = datetime.fromisoformat(ts_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def _parse_iso8601_as_kst(ts_str: str | None) -> datetime:
    """
    Cafe24 응답의 ISO8601 시간 문자열을 UTC+9(KST)로 변환한다.
    예: '2025-10-29T12:34:56.123' -> 2025-10-29 12:34:56.123+09:00
    """
    if ts_str is None:
        return datetime.now(KST)

    dt = datetime.fromisoformat(ts_str)

    # 응답이 타임존 없는 naive datetime인 경우 → 한국 시간대 지정
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    else:
        # 응답이 UTC 기반이라면 KST로 변환
        dt = dt.astimezone(KST)

    return dt

class TokenStoreError(Exception):
    pass

def upsert_token(token_json: Dict[str, Any]):
    """
    Cafe24에서 받은 token_json(발급/재발급 둘 다)을
    cafe24.oauth_tokens 테이블에 mall_id 단위로 upsert.
    """
    cfg = get_cafe24_config()

    access_token = token_json["access_token"]
    refresh_token = token_json["refresh_token"]

    token_type = token_json.get("token_type") or "bearer"
    client_id  = token_json.get("client_id")
    mall_id    = token_json.get("mall_id") or cfg["mall_id"]
    user_id    = token_json.get("user_id")
    scopes_val = token_json.get("scopes", [])  # list[str]

    issued_at_dt = _parse_iso8601_as_kst(token_json.get("issued_at"))
    expires_at_dt = _parse_iso8601_as_kst(token_json["expires_at"])
    refresh_token_expires_at_dt = _parse_iso8601_as_kst(
        token_json["refresh_token_expires_at"]
    )

    updated_at_dt = now_utc()
    status_val = "active"

    params = (
        access_token,
        expires_at_dt,
        refresh_token,
        refresh_token_expires_at_dt,
        client_id,
        mall_id,
        user_id,
        scopes_val,
        token_type,
        issued_at_dt,
        updated_at_dt,
        status_val,
    )

    row = execute_upsert_token(params)
    return row