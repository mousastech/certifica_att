"""
Segurança: hashing de senha (bcrypt) e tokens JWT (multi-tenant).

O JWT carrega o tenant (tid/tslug) e os papéis (adm = admin do tenant,
sa = superadmin da plataforma). É stateless: o contexto de tenant viaja no token.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request

from app.config import get_settings
from app.models.schemas import UserPublic

logger = logging.getLogger(__name__)


# ── Senhas ────────────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def is_superadmin(email: str) -> bool:
    """APENAS o bootstrap por env (SUPERADMIN_EMAILS) — NÃO é a fonte única de verdade.

    Um superadmin também é qualquer usuário do tenant 'platform': essa derivação
    acontece na emissão do token (auth.py::_token_and_user faz o OR com o slug do
    tenant). Portanto operadores criados na UI (/platform) viram superadmin ao logar,
    mesmo sem estar nesta env. Use esta função só para o 1º operador (seed/lockout).
    """
    return bool(email) and email.lower() in get_settings().superadmin_emails_list


# ── JWT ─────────────────────────────────────────────────────────────────────
def create_token(email: str, name: str, tenant_id: Optional[str], tenant_slug: Optional[str],
                 is_admin: bool = False, is_superadmin: bool = False,
                 must_change: bool = False) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": email.lower(), "nm": name, "tid": tenant_id, "tslug": tenant_slug,
         "adm": is_admin, "sa": is_superadmin, "must_change": must_change, "exp": expire},
        s.JWT_SECRET, algorithm="HS256",
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, get_settings().JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None


def _token_from_request(request: Request) -> Optional[str]:
    # O gateway do Databricks Apps consome o Authorization para o próprio OAuth,
    # então o JWT do app trafega em X-Santander-Auth.
    x = request.headers.get("X-Santander-Auth", "")
    if x:
        return x[7:].strip() if x.startswith("Bearer ") else x.strip()
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


# ── Dependencies ──────────────────────────────────────────────────────────────
def get_current_user(request: Request) -> UserPublic:
    """Exige JWT válido. O contexto de tenant vem do próprio token."""
    s = get_settings()
    if not s.ENABLE_JWT_AUTH:
        return UserPublic(email="anon@local", name="Anônimo", tenant_id=None,
                          is_admin=True, is_superadmin=True)

    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    p = decode_token(token)
    if not p or not p.get("sub"):
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return UserPublic(
        email=p["sub"], name=p.get("nm") or p["sub"], tenant_id=p.get("tid"),
        tenant_slug=p.get("tslug"), is_admin=bool(p.get("adm")),
        is_superadmin=bool(p.get("sa")), must_change_password=bool(p.get("must_change")),
    )


def require_admin(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    if not (user.is_admin or user.is_superadmin):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin")
    # Revogação imediata do papel de admin: se o token diz admin mas o DB já não
    # (rebaixado via toggle), nega na hora sem esperar o JWT de 12h. Superadmin e
    # o modo sem-auth (usuário sintético) passam direto.
    if (get_settings().ENABLE_JWT_AUTH and user.is_admin and not user.is_superadmin):
        from app.services import users as users_svc
        row = users_svc.get_user(user.tenant_id, user.email)
        if not row or not row.get("is_admin"):
            raise HTTPException(status_code=403, detail="Acesso de admin revogado")
    return user


def require_superadmin(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    if not user.is_superadmin:
        raise HTTPException(status_code=403, detail="Acesso restrito à plataforma")
    # Revogação imediata: um superadmin derivado do vínculo ao tenant 'platform'
    # (operador criado na UI) perde o acesso assim que é removido — sem esperar o
    # JWT de 12h expirar. Bootstrap por env (SUPERADMIN_EMAILS) nunca é revogado,
    # e o modo sem auth (dev/demo, usuário sintético anon@local) também não checa.
    if get_settings().ENABLE_JWT_AUTH and not is_superadmin(user.email):
        from app.services import tenants as tenants_svc, users as users_svc
        platform = tenants_svc.get_tenant_by_slug(get_settings().PLATFORM_TENANT_SLUG)
        if not platform or not users_svc.get_user(platform["id"], user.email):
            raise HTTPException(status_code=403, detail="Operador removido; sessão revogada")
    return user
