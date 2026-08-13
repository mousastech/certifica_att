"""
Camada de acesso ao Postgres.

Em MOCK_MODE não há conexão — os repositórios usam o seed em memória.
Em produção a senha do Postgres é resolvida nesta ordem:
  1. PGPASSWORD .............. senha estática (dev / Secrets Manager)
  2. RDS_IAM_AUTH=true ....... token IAM de curta duração (AWS RDS, via boto3)
  3. LAKEBASE_ENDPOINT ....... credencial OAuth do Databricks (Lakebase / Databricks Apps)

Deploy atual: Databricks Apps + Lakebase (caminho 3). Os caminhos AWS (1/2) ficam
disponíveis para um eventual host fora do Databricks.
"""
import logging
import sys
import threading
import time
from contextlib import contextmanager
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# cache da credencial de curta duração (Lakebase OAuth ~1h / RDS IAM ~15min).
_pw_cache: dict = {"token": None, "exp": 0.0}

# ── Connection pool ───────────────────────────────────────────────────────────
# Um pool psycopg reaproveita conexões (evita TCP+TLS+auth a cada request) no hot
# path — inclusive nas checagens de revogação de admin/superadmin. Duas armadilhas
# do Lakebase são tratadas: (1) a senha é uma credencial OAuth que ROTACIONA, então
# o pool é chaveado pela credencial e reconstruído quando ela muda; (2) a instância
# PARA SOZINHA quando ociosa, então validamos a conexão (`check`) antes de entregar
# e caímos numa conexão direta se o pool não puder servir.
_pool = None
_pool_token: Optional[str] = None
_pool_lock = threading.Lock()


def _db_password(s) -> Optional[str]:
    """Resolve a senha do Postgres conforme a estratégia configurada."""
    if s.PGPASSWORD:
        return s.PGPASSWORD

    now = time.time()
    if _pw_cache["token"] and _pw_cache["exp"] - now > 120:
        return _pw_cache["token"]

    # AWS RDS — token IAM via boto3
    if s.RDS_IAM_AUTH:
        import boto3
        client = boto3.client("rds", region_name=s.AWS_REGION)
        token = client.generate_db_auth_token(
            DBHostname=s.PGHOST, Port=s.PGPORT, DBUsername=s.PGUSER, Region=s.AWS_REGION,
        )
        _pw_cache["token"] = token
        _pw_cache["exp"] = now + 780          # 13 min
        return token

    # Databricks Lakebase (Database Instance) — credencial OAuth gerada pela
    # identidade do app (service principal) para a instância configurada.
    if s.LAKEBASE_INSTANCE_NAME:
        import uuid as _uuid
        from app.auth.workspace_client import get_workspace_client
        cred = get_workspace_client().database.generate_database_credential(
            request_id=str(_uuid.uuid4()),
            instance_names=[s.LAKEBASE_INSTANCE_NAME],
        )
        _pw_cache["token"] = cred.token
        _pw_cache["exp"] = now + 2700          # 45 min
        return cred.token

    return None


def _conninfo(s, password: str) -> str:
    from psycopg.conninfo import make_conninfo
    return make_conninfo(
        host=s.PGHOST, port=s.PGPORT, dbname=s.PGDATABASE,
        user=s.PGUSER, password=password or "",
        sslmode=s.PGSSLMODE, options=f"-c search_path={s.PGSCHEMA}",
        connect_timeout=15,
    )


def _get_pool(password: str):
    """Devolve o pool para a credencial atual, reconstruindo se a senha rotacionou."""
    global _pool, _pool_token
    if _pool is not None and _pool_token == password:
        return _pool
    with _pool_lock:
        if _pool is not None and _pool_token == password:
            return _pool
        # credencial mudou (rotação OAuth) — fecha o pool antigo e cria um novo
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass
            _pool = None
        from psycopg_pool import ConnectionPool
        s = get_settings()
        pool = ConnectionPool(
            conninfo=_conninfo(s, password),
            min_size=1, max_size=8,
            # recicla antes da expiração do token OAuth (~45min de cache) e valida
            # a conexão ao emprestar (Lakebase pode ter parado por ociosidade).
            max_lifetime=1800, max_idle=300, timeout=20,
            check=ConnectionPool.check_connection,
            kwargs={"autocommit": True},
            open=True, name="certifica",
        )
        _pool, _pool_token = pool, password
        logger.info("Postgres connection pool inicializado (max_size=8)")
        return pool


@contextmanager
def get_conn():
    """Conexão Postgres do pool (reaproveitada); gera credencial fresca quando necessário.

    Fallback: se o pool não puder emprestar uma conexão (ex.: Lakebase reiniciando),
    abre uma conexão direta de curta duração para não derrubar o request. O fallback
    cobre apenas a AQUISIÇÃO — uma vez emprestada, erros do caller sobem normalmente.
    """
    s = get_settings()
    password = _db_password(s) or ""

    # 1) tenta emprestar do pool; se a aquisição falhar, vai p/ conexão direta.
    pooled_cm = None
    conn = None
    try:
        pooled_cm = _get_pool(password).connection()
        conn = pooled_cm.__enter__()
    except Exception as e:
        logger.warning(f"Pool indisponível ({e}); usando conexão direta.")
        pooled_cm = None
        import psycopg
        conn = psycopg.connect(_conninfo(s, password), autocommit=True)

    # 2) entrega a conexão; a limpeza depende da origem (pool vs direta).
    if pooled_cm is not None:
        try:
            conn.autocommit = True
            yield conn
        except BaseException:
            pooled_cm.__exit__(*sys.exc_info())
            raise
        else:
            pooled_cm.__exit__(None, None, None)
    else:
        try:
            yield conn
        finally:
            conn.close()


def close_pool() -> None:
    """Fecha o pool (chamado no shutdown do app)."""
    global _pool, _pool_token
    with _pool_lock:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass
            _pool, _pool_token = None, None


def is_db_ready() -> bool:
    s = get_settings()
    if s.MOCK_MODE:
        return False
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:  # pragma: no cover
        logger.warning(f"Postgres indisponível: {e}")
        return False
