"""
This function handles the Cafe24 OAuth token isuue process.
"""
import os
from responses import json_response
from cafe24_oauth import request_token_with_code, Cafe24APIError
from token_store import upsert_token, TokenStoreError
from db import DBError, now_utc, fetch_latest_authorization_code

def lambda_handler(event, context):
    """
    1) API Gateway -> Lambda 호출
    2) queryStringParameters.code 에 authorization_code가 들어왔다고 가정
       ex) /token/issue?code=XXXXX
    3) Cafe24에 토큰 발급 요청 -> DB upsert -> 결과 반환
    """
    if os.environ.get("AWS_EXECUTION_ENV") is None:
        # 로컬이라고 판단
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=".env.local")
        except Exception as e:
            print("dotenv load skipped or failed:", e)

    try:
        latest = fetch_latest_authorization_code()
        auth_code = latest["code"]
        # state = latest["state"]  # 지금은 안 씀, 필요하면 로깅만
    except DBError as e:
        return json_response(500, {
            "ok": False,
            "message": "No authorization code available",
            "error": str(e),
        })
    except Exception as e:
        return json_response(500, {
            "ok": False,
            "message": "Failed to load authorization code from DB",
            "error": str(e),
        })

    try:
        token_json = request_token_with_code(auth_code)
    except Cafe24APIError as e:
        return json_response(500, {
            "ok": False,
            "message": "Cafe24 config error",
            "error": str(e),
        })
    except Exception as e:
        return json_response(502, {
            "ok": False,
            "message": "Failed to obtain token from Cafe24",
            "error": str(e),
        })

    try:
        row = upsert_token(token_json)
    except (TokenStoreError, DBError) as e:
        return json_response(500, {
            "ok": False,
            "message": "Failed to store token to DB",
            "error": str(e),
        })
    except Exception as e:
        return json_response(500, {
            "ok": False,
            "message": "Unexpected DB error",
            "error": str(e),
        })

    return json_response(200, {
        "ok": True,
        "message": "Access token stored/updated",
        "data": {
            "token_row_id": row["id"],
            "mall_id": row["mall_id"],
            "issued_at": row["issued_at"],
            "expires_at": row["expires_at"],
            "at": now_utc().isoformat(),
        }
    })