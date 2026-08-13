"""
WorkspaceClient — OAuth M2M do service principal (Lakebase, default), ou
on-behalf-of-user (OBO) para chamadas de LLM com a identidade do usuário logado.

Em Databricks Apps o proxy injeta o token do usuário no header
`X-Forwarded-Access-Token` a cada request. Guardamos esse token num contextvar
por request e o usamos para consultar os serving endpoints — assim as chamadas
ao Claude/GPT-5 usam a permissão do usuário (não a do SP do app, que pode não
ter acesso a esses modelos). O acesso ao Lakebase continua via o SP do app.
"""
import contextvars
import logging
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)

# Token do usuário logado (OBO), populado por middleware a cada request.
_user_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "databricks_user_token", default=None,
)


def set_user_token(token: str | None) -> None:
    _user_token.set(token or None)


def get_user_token() -> str | None:
    return _user_token.get()


@lru_cache()
def get_workspace_client():
    from databricks.sdk import WorkspaceClient

    s = get_settings()

    # Em Databricks Apps, DATABRICKS_HOST/CLIENT_ID/CLIENT_SECRET são injetados.
    if s.DATABRICKS_CLIENT_ID and s.DATABRICKS_CLIENT_SECRET:
        logger.info("WorkspaceClient via OAuth M2M (service principal)")
        return WorkspaceClient(
            host=s.databricks_host,
            client_id=s.DATABRICKS_CLIENT_ID,
            client_secret=s.DATABRICKS_CLIENT_SECRET,
        )
    if s.DATABRICKS_TOKEN:
        logger.info("WorkspaceClient via PAT")
        return WorkspaceClient(host=s.databricks_host, token=s.DATABRICKS_TOKEN)

    # Fallback: configuração padrão (CLI profile / env)
    logger.info("WorkspaceClient via default config (CLI/env)")
    return WorkspaceClient()


def get_llm_client():
    """Cliente para consultar serving endpoints (LLM).

    Prefere OBO (token do usuário logado) quando disponível — assim usa a
    permissão do usuário para Claude/GPT-5. Sem token de usuário (ex.: dev,
    ou header ausente), cai no cliente do service principal."""
    token = get_user_token()
    if token:
        from databricks.sdk import WorkspaceClient
        return WorkspaceClient(host=get_settings().databricks_host, token=token)
    return get_workspace_client()
