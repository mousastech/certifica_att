"""
Convites de acesso — link com token para primeiro acesso (o convidado define a senha).

Fluxo: um operador (ao criar tenant) ou um admin de tenant gera um convite → token
opaco → link /invite/{token}. O convidado abre, vê o branding do tenant, define a
senha e a conta é criada e ativada. Token é de uso único e expira.

Postgres em produção, dict em memória no MOCK_MODE.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import get_settings
from app.services import users as users_svc

logger = logging.getLogger(__name__)

# store em memória para dev (MOCK_MODE): token -> dict
_mem: dict[str, dict] = {}

INVITE_TTL_DAYS = 7


def _use_db() -> bool:
    return not get_settings().MOCK_MODE


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_invite(tenant_id: str, email: str, name: str, is_admin: bool = False,
                  invited_by: Optional[str] = None, ttl_days: int = INVITE_TTL_DAYS) -> dict:
    """Cria um convite e devolve o registro (inclui o token). Uso único."""
    email = email.strip().lower()
    token = secrets.token_urlsafe(32)
    expires = _now() + timedelta(days=ttl_days)
    rec = {"token": token, "tenant_id": tenant_id, "email": email, "name": name.strip(),
           "is_admin": is_admin, "invited_by": invited_by, "expires_at": expires,
           "accepted_at": None}
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO invites (token,tenant_id,email,name,is_admin,invited_by,expires_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (token, tenant_id, email, name.strip(), is_admin, invited_by, expires),
            )
    else:
        _mem[token] = rec
    logger.info(f"Convite criado: {email} @ {tenant_id} (admin={is_admin})")
    return rec


def get_invite(token: str) -> Optional[dict]:
    """Devolve o convite bruto (sem validar), ou None se não existe."""
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute(
                "SELECT token,tenant_id,email,name,is_admin,invited_by,expires_at,accepted_at "
                "FROM invites WHERE token=%s", (token,)
            ).fetchone()
        if not r:
            return None
        return {"token": r[0], "tenant_id": r[1], "email": r[2], "name": r[3],
                "is_admin": r[4], "invited_by": r[5], "expires_at": r[6], "accepted_at": r[7]}
    return _mem.get(token)


def invite_state(inv: Optional[dict]) -> str:
    """'valid' | 'not_found' | 'accepted' | 'expired'."""
    if not inv:
        return "not_found"
    if inv.get("accepted_at"):
        return "accepted"
    exp = inv.get("expires_at")
    if exp and exp < _now():
        return "expired"
    return "valid"


def accept_invite(token: str, password_hash: str) -> Optional[dict]:
    """Consome um convite válido: cria o usuário e marca accepted_at.

    Retorno:
      - dict com dados p/ emitir o token de sessão (sucesso);
      - {"error": "exists"} se já há conta com esse e-mail no tenant (não sobrescreve
        senha nem promove: o admin deve usar o toggle de admin, não um convite);
      - None se o convite é inválido/expirado/já consumido (inclui perder a corrida).
    """
    inv = get_invite(token)
    if invite_state(inv) != "valid":
        return None
    assert inv is not None
    # Não aceitar convite para e-mail que já é conta: evita escalonamento (o convite
    # carrega is_admin) e descarte silencioso da senha digitada (create_user faz
    # ON CONFLICT DO NOTHING). Rejeita explicitamente.
    if users_svc.get_user(inv["tenant_id"], inv["email"]):
        return {"error": "exists"}
    # Consumo atômico e de uso único: só prossegue quem conseguir marcar accepted_at
    # (fecha a janela de dois accepts concorrentes com o mesmo token).
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            row = conn.execute(
                "UPDATE invites SET accepted_at=now() "
                "WHERE token=%s AND accepted_at IS NULL RETURNING token", (token,)
            ).fetchone()
        if not row:
            return None
    else:
        if _mem[token].get("accepted_at"):
            return None
        _mem[token]["accepted_at"] = _now()
    users_svc.create_user(inv["tenant_id"], inv["email"], inv["name"], password_hash,
                          is_admin=bool(inv["is_admin"]), must_change_password=False)
    return {"tenant_id": inv["tenant_id"], "email": inv["email"], "name": inv["name"],
            "is_admin": bool(inv["is_admin"])}
