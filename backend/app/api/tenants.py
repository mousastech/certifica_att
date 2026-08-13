"""
Endpoints de tenants: tema público (branding), signup self-service e
consola da plataforma (superadmin) para provisionar/listar clientes.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

import re

from app.config import get_settings
from app.models.schemas import (
    ThemeResponse, TenantPublic, SignupRequest, TenantCreate, TenantStatusUpdate,
    TenantBrandingUpdate, TokenResponse, UserPublic, Operator, OperatorCreate,
    ProgramContent, RoutesContent, InviteInfo, InviteAccept, InviteCreated, InviteCreate,
)
from app.auth import security
from app.services import tenants as tenants_svc, users as users_svc, invites as invites_svc

logger = logging.getLogger(__name__)
router = APIRouter()
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _platform_tenant_id() -> str:
    slug = get_settings().PLATFORM_TENANT_SLUG
    t = tenants_svc.get_tenant_by_slug(slug)
    if not t:
        raise HTTPException(500, "Tenant de plataforma não inicializado")
    return t["id"]


# ── Programa del tenant (página de introducción post-login) ───────────────────
def _can_edit_program(user: UserPublic, slug: str) -> bool:
    return user.is_superadmin or (user.is_admin and (user.tenant_slug or "").lower() == slug.lower())


@router.get("/tenants/{slug}/program", response_model=ProgramContent)
async def get_program(slug: str, user: UserPublic = Depends(security.get_current_user)):
    if not (user.is_superadmin or (user.tenant_slug or "").lower() == slug.lower()):
        raise HTTPException(403, "Sin acceso al programa de este tenant")
    return ProgramContent(**tenants_svc.get_program(slug))


@router.put("/tenants/{slug}/program", response_model=ProgramContent)
async def put_program(slug: str, body: ProgramContent,
                      user: UserPublic = Depends(security.get_current_user)):
    if not _can_edit_program(user, slug):
        raise HTTPException(403, "Sin permiso para editar el programa")
    if not tenants_svc.get_tenant_by_slug(slug):
        raise HTTPException(404, "Tenant não encontrado")
    tenants_svc.set_program(slug, body.model_dump())
    return body


@router.get("/tenants/{slug}/routes", response_model=RoutesContent)
async def get_routes(slug: str, user: UserPublic = Depends(security.get_current_user)):
    if not (user.is_superadmin or (user.tenant_slug or "").lower() == slug.lower()):
        raise HTTPException(403, "Sin acceso a las rutas de este tenant")
    return RoutesContent(**tenants_svc.get_routes(slug))


@router.put("/tenants/{slug}/routes", response_model=RoutesContent)
async def put_routes(slug: str, body: RoutesContent,
                     user: UserPublic = Depends(security.get_current_user)):
    if not _can_edit_program(user, slug):
        raise HTTPException(403, "Sin permiso para editar las rutas")
    if not tenants_svc.get_tenant_by_slug(slug):
        raise HTTPException(404, "Tenant não encontrado")
    tenants_svc.set_routes(slug, body.model_dump())
    return body


@router.get("/tenants/resolve")
async def resolve_tenant(q: str):
    """Resuelve nombre o slug de empresa → slug (para el Landing 'buscar tu espacio')."""
    slug = tenants_svc.resolve_slug(q)
    if not slug:
        raise HTTPException(404, "Tenant não encontrado")
    return {"slug": slug}


# ── Branding público (resolve antes do login para brandear a tela) ────────────
@router.get("/tenants/{slug}/theme", response_model=ThemeResponse)
async def theme(slug: str):
    t = tenants_svc.get_tenant_by_slug(slug)
    if not t or t.get("status") != "active":
        raise HTTPException(404, "Tenant não encontrado")
    return ThemeResponse(slug=t["slug"], name=t["name"], primary_color=t["primary_color"],
                         logo_url=t.get("logo_url"),
                         allow_self_register=t.get("allow_self_register", True),
                         pass_mark=t.get("pass_mark", 70))


# ── Signup self-service: cria tenant + primeiro admin ─────────────────────────
@router.post("/tenants/signup", response_model=TokenResponse)
async def signup(data: SignupRequest):
    if tenants_svc.get_tenant_by_slug(data.slug):
        raise HTTPException(409, "Esse identificador (slug) já está em uso.")
    email = data.admin_email.strip().lower()
    if "@" not in email or len(data.admin_password) < 6:
        raise HTTPException(422, "E-mail válido e senha de 6+ caracteres são obrigatórios.")

    tenant = tenants_svc.create_tenant(
        slug=data.slug, name=data.company, primary_color=data.primary_color,
        logo_url=data.logo_url, email_domain=data.email_domain,
    )
    users_svc.create_user(tenant["id"], email, data.admin_name.strip() or email,
                          security.hash_password(data.admin_password), is_admin=True)
    sa = security.is_superadmin(email)
    token = security.create_token(email, data.admin_name.strip() or email,
                                  tenant["id"], tenant["slug"], is_admin=True, is_superadmin=sa)
    user = UserPublic(email=email, name=data.admin_name.strip() or email,
                      tenant_id=tenant["id"], tenant_slug=tenant["slug"],
                      is_admin=True, is_superadmin=sa)
    return TokenResponse(access_token=token, user=user)


# ── Consola da plataforma (superadmin) ────────────────────────────────────────
@router.get("/platform/tenants", response_model=List[TenantPublic])
async def list_tenants(_: UserPublic = Depends(security.require_superadmin)):
    return [TenantPublic(**t) for t in tenants_svc.list_tenants()]


# ── Operadores da plataforma (usuários administrativos do tenant 'platform') ──
@router.get("/platform/operators", response_model=List[Operator])
async def list_operators(_: UserPublic = Depends(security.require_superadmin)):
    tid = _platform_tenant_id()
    return [Operator(email=u["email"], name=u["name"], created_at=u.get("created_at"))
            for u in users_svc.list_users(tid)]


@router.post("/platform/operators", response_model=Operator)
async def create_operator(data: OperatorCreate, _: UserPublic = Depends(security.require_superadmin)):
    tid = _platform_tenant_id()
    email = data.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(422, "E-mail inválido")
    if len(data.password) < 6:
        raise HTTPException(422, "A senha deve ter ao menos 6 caracteres")
    if not data.name.strip():
        raise HTTPException(422, "Nome obrigatório")
    if users_svc.get_user(tid, email):
        raise HTTPException(409, "Operador já existe")
    users_svc.create_user(tid, email, data.name.strip(),
                          security.hash_password(data.password), is_admin=True)
    return Operator(email=email, name=data.name.strip())


@router.delete("/platform/operators/{email}")
async def delete_operator(email: str, admin: UserPublic = Depends(security.require_superadmin)):
    tid = _platform_tenant_id()
    email = email.lower()
    if email == admin.email.lower():
        raise HTTPException(400, "Você não pode remover a própria conta")
    if len(users_svc.list_users(tid)) <= 1:
        raise HTTPException(400, "Deve existir ao menos um operador")
    if not users_svc.get_user(tid, email):
        raise HTTPException(404, "Operador não encontrado")
    users_svc.delete_user(tid, email)
    return {"ok": True}


@router.post("/platform/tenants", response_model=TenantPublic)
async def create_tenant(data: TenantCreate, _: UserPublic = Depends(security.require_superadmin)):
    if tenants_svc.get_tenant_by_slug(data.slug):
        raise HTTPException(409, "slug já existe")
    t = tenants_svc.create_tenant(
        slug=data.slug, name=data.name, primary_color=data.primary_color,
        logo_url=data.logo_url, pass_mark=data.pass_mark,
        allow_self_register=data.allow_self_register, email_domain=data.email_domain,
    )
    if data.admin_email and data.admin_password:
        users_svc.create_user(t["id"], data.admin_email.strip().lower(),
                              data.admin_name or data.admin_email,
                              security.hash_password(data.admin_password), is_admin=True)
    full = next((x for x in tenants_svc.list_tenants() if x["id"] == t["id"]), t)
    return TenantPublic(**full)


@router.patch("/platform/tenants/{slug}", response_model=TenantPublic)
async def update_tenant_branding(slug: str, body: TenantBrandingUpdate,
                                 _: UserPublic = Depends(security.require_superadmin)):
    if not tenants_svc.get_tenant_by_slug(slug):
        raise HTTPException(404, "Tenant não encontrado")
    tenants_svc.update_branding(slug, name=body.name, primary_color=body.primary_color,
                                logo_url=body.logo_url)
    full = next((x for x in tenants_svc.list_tenants() if x["slug"] == slug.lower()), None)
    return TenantPublic(**full)


@router.patch("/platform/tenants/{slug}/status", response_model=TenantPublic)
async def set_tenant_status(slug: str, body: TenantStatusUpdate,
                            _: UserPublic = Depends(security.require_superadmin)):
    if body.status not in ("active", "suspended"):
        raise HTTPException(422, "status inválido")
    if not tenants_svc.get_tenant_by_slug(slug):
        raise HTTPException(404, "Tenant não encontrado")
    tenants_svc.set_status(slug, body.status)
    full = next((x for x in tenants_svc.list_tenants() if x["slug"] == slug.lower()), None)
    if not full:
        raise HTTPException(404, "Tenant não encontrado")
    return TenantPublic(**full)


# ── Convites de acesso (link de primeiro acesso) ──────────────────────────────
def _make_invite(tenant: dict, email: str, name: str, is_admin: bool,
                 invited_by: str) -> InviteCreated:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(422, "E-mail inválido")
    if not name.strip():
        raise HTTPException(422, "Nome obrigatório")
    if users_svc.get_user(tenant["id"], email):
        raise HTTPException(409, "E-mail já cadastrado neste tenant")
    inv = invites_svc.create_invite(tenant["id"], email, name, is_admin=is_admin,
                                    invited_by=invited_by)
    exp = inv["expires_at"]
    return InviteCreated(token=inv["token"], invite_path=f"/invite/{inv['token']}",
                         email=email, expires_at=exp.isoformat() if exp else None)


@router.post("/platform/tenants/{slug}/invite", response_model=InviteCreated)
async def platform_invite(slug: str, body: InviteCreate,
                          admin: UserPublic = Depends(security.require_superadmin)):
    """Operador gera um convite (normalmente o 1º admin) para um tenant recém-criado."""
    tenant = tenants_svc.get_tenant_by_slug(slug)
    if not tenant:
        raise HTTPException(404, "Tenant não encontrado")
    return _make_invite(tenant, body.email, body.name, is_admin=body.is_admin,
                        invited_by=admin.email)


@router.post("/admin/invite", response_model=InviteCreated)
async def admin_invite(body: InviteCreate, admin: UserPublic = Depends(security.require_admin)):
    """Admin de um tenant convida um usuário/admin para o SEU próprio tenant."""
    tenant = tenants_svc.get_tenant_by_id(admin.tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant não encontrado")
    return _make_invite(tenant, body.email, body.name, is_admin=body.is_admin,
                        invited_by=admin.email)


@router.get("/invite/{token}", response_model=InviteInfo)
async def invite_info(token: str):
    """Público: dados do convite + branding do tenant para a tela de aceite."""
    inv = invites_svc.get_invite(token)
    state = invites_svc.invite_state(inv)
    if state == "not_found" or not inv:
        return InviteInfo(state="not_found")
    tenant = tenants_svc.get_tenant_by_id(inv["tenant_id"])
    # Tenant suspenso/removido: não vaza branding — trata como convite indisponível.
    if not tenant or tenant.get("status") != "active":
        return InviteInfo(state="not_found")
    return InviteInfo(
        state=state, email=inv["email"], name=inv["name"], is_admin=bool(inv["is_admin"]),
        tenant_slug=tenant["slug"], tenant_name=tenant["name"],
        primary_color=tenant.get("primary_color"), logo_url=tenant.get("logo_url"),
    )


@router.post("/invite/{token}/accept", response_model=TokenResponse)
async def invite_accept(token: str, body: InviteAccept):
    """Público: o convidado define a senha; a conta é criada e logada."""
    if len(body.password) < 6:
        raise HTTPException(422, "A senha deve ter ao menos 6 caracteres")
    # Não deixar entrar por convite num tenant suspenso (o /login também recusa).
    inv = invites_svc.get_invite(token)
    if invites_svc.invite_state(inv) == "valid":
        tn = tenants_svc.get_tenant_by_id(inv["tenant_id"])
        if not tn or tn.get("status") != "active":
            raise HTTPException(403, "Espaço indisponível. Contate o administrador.")
    result = invites_svc.accept_invite(token, security.hash_password(body.password))
    if not result:
        raise HTTPException(410, "Convite inválido, expirado ou já utilizado")
    if result.get("error") == "exists":
        raise HTTPException(409, "Já existe uma conta com este e-mail. Faça login.")
    tenant = tenants_svc.get_tenant_by_id(result["tenant_id"])
    slug = tenant["slug"] if tenant else None
    sa = security.is_superadmin(result["email"]) or slug == get_settings().PLATFORM_TENANT_SLUG
    tok = security.create_token(result["email"], result["name"], result["tenant_id"], slug,
                                is_admin=result["is_admin"], is_superadmin=sa)
    user = UserPublic(email=result["email"], name=result["name"],
                      tenant_id=result["tenant_id"], tenant_slug=slug,
                      is_admin=result["is_admin"], is_superadmin=sa)
    return TokenResponse(access_token=tok, user=user)
