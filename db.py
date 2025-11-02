"""
This moudle provides database access functions for Cafe24 Oauth tokens.
"""
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row
from settings import get_pg_config

class DBError(Exception):
    pass

def _dsn_from_env():
    """
    Constructs the Postgres DSN from environment variables.
    """
    cfg = get_pg_config()
    if not all([cfg["host"], cfg["port"], cfg["user"], cfg["password"], cfg["database"]]):
        raise DBError("Database environment variables are not fully set")
    return (
        f"postgresql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )
    
def fetch_latest_authorization_code():
    """
    oauth_authorization_codes 테이블에서 가장 최근 code/state를 가져온다.
    mall_id 없이 단일 몰 기준으로 동작한다고 가정.
    """
    sql = """
        SELECT code, state
        FROM cafe24.authorization_codes
        ORDER BY received_at DESC
        LIMIT 1;
    """

    dsn = _dsn_from_env()
    with psycopg.connect(dsn, sslmode="require", row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        raise DBError("No authorization_code found in authorization_codes")

    return row  # {"code": "...", "state": "..."}
    

def execute_upsert_token(params_tuple):
    """
    params_tuple 순서는 token_store.upsert_token()에서 만들어서 넘김.
    실제 upsert SQL만 여기서 실행.
    """
    upsert_sql = """
        INSERT INTO cafe24.oauth_tokens (
            access_token,
            expires_at,
            refresh_token,
            refresh_token_expires_at,
            client_id,
            mall_id,
            user_id,
            scopes,
            token_type,
            issued_at,
            updated_at,
            status
        )
        VALUES (
            %s,  -- access_token
            %s,  -- expires_at
            %s,  -- refresh_token
            %s,  -- refresh_token_expires_at
            %s,  -- client_id
            %s,  -- mall_id
            %s,  -- user_id
            %s,  -- scopes
            %s,  -- token_type
            %s,  -- issued_at
            %s,  -- updated_at
            %s   -- status
        )
        ON CONFLICT (mall_id)
        DO UPDATE SET
            access_token             = EXCLUDED.access_token,
            expires_at               = EXCLUDED.expires_at,
            refresh_token            = EXCLUDED.refresh_token,
            refresh_token_expires_at = EXCLUDED.refresh_token_expires_at,
            client_id                = EXCLUDED.client_id,
            user_id                  = EXCLUDED.user_id,
            scopes                   = EXCLUDED.scopes,
            token_type               = EXCLUDED.token_type,
            issued_at                = EXCLUDED.issued_at,
            updated_at               = EXCLUDED.updated_at,
            status                   = EXCLUDED.status
        RETURNING id, mall_id, issued_at, expires_at;
    """

    dsn = _dsn_from_env()
    with psycopg.connect(dsn, sslmode="require", row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(upsert_sql, params_tuple)
            row = cur.fetchone()
            conn.commit()
    return row

def fetch_refresh_token_for_mall(mall_id: str):
    """
    재발급 시 현재 refresh_token을 가져오기 위한 쿼리.
    """
    sql = """
        SELECT refresh_token
        FROM cafe24.oauth_tokens
        WHERE mall_id = %s
        AND status = 'active'
        ORDER BY updated_at DESC
        LIMIT 1;
    """
    dsn = _dsn_from_env()
    with psycopg.connect(dsn, sslmode="require", row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (mall_id,))
            row = cur.fetchone()
    if not row:
        raise DBError("No active refresh_token for mall_id")
    return row["refresh_token"]

def now_utc():
    """
    Returns the current UTC datetime.
    """
    return datetime.now(timezone.utc)