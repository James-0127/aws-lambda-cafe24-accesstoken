"""
This module handles Cafe24 Oauth token requests.
"""

import json
import base64
import urllib.parse
import urllib.request
from settings import get_cafe24_config
from db import fetch_refresh_token_for_mall

class Cafe24APIError(Exception):
    pass

def _basic_auth_header(client_id: str, client_secret: str) -> str:
    creds = f"{client_id}:{client_secret}"
    enc = base64.b64encode(creds.encode("utf-8")).decode("utf-8")
    print(enc)
    return f"Basic {enc}"

def _post_form(url: str, headers: dict, data_dict: dict, timeout_sec: int = 10) -> dict:
    body = urllib.parse.urlencode(data_dict).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)

def request_token_with_code(auth_code: str) -> dict:
    """
    grant_type=authorization_code
    Cafe24에서 최초 access_token/refresh_token 발급
    """
    cfg = get_cafe24_config()
    if not all([cfg["mall_id"], cfg["client_id"], cfg["client_secret"], cfg["redirect_uri"]]):
        raise Cafe24APIError("Cafe24 config not set properly")

    token_url = f"https://{cfg['mall_id']}.cafe24api.com/api/v2/oauth/token"

    headers = {
        "Authorization": _basic_auth_header(cfg["client_id"], cfg["client_secret"]),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": cfg["redirect_uri"],
    }

    return _post_form(token_url, headers, payload)

def request_token_with_refresh() -> dict:
    """
    grant_type=refresh_token
    Cafe24에서 access_token/refresh_token 재발급
    - 현재 mall_id의 refresh_token은 DB에서 읽어온다.
    """
    cfg = get_cafe24_config()
    if not all([cfg["mall_id"], cfg["client_id"], cfg["client_secret"]]):
        raise Cafe24APIError("Cafe24 config not set properly")

    mall_id = cfg["mall_id"]
    refresh_token = fetch_refresh_token_for_mall(mall_id)

    token_url = f"https://{mall_id}.cafe24api.com/api/v2/oauth/token"

    headers = {
        "Authorization": _basic_auth_header(cfg["client_id"], cfg["client_secret"]),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    return _post_form(token_url, headers, payload)