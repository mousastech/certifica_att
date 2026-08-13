"""
Grupos / áreas (personas) e resolução de trilhas visíveis por usuário.

Um *grupo* (CDO, CSO, Finanças-Genie, ...) recebe um conjunto de trilhas
(`track_keys`) e, opcionalmente, simulados (`certification_ids`). Cada usuário
pertence a um grupo (`users.group_key`) e pode ter trilhas extras
(`users.extra_track_keys`) — personalização por usuário.

`visible_tracks_for_user` é o resolvedor central usado pela app do trainee:
devolve as trilhas e simulados que aquele usuário deve ver.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from app.config import get_settings
from app.services import tenants as tenants_svc

logger = logging.getLogger(__name__)

# store em memória p/ MOCK_MODE: tenant_id -> {key -> group}
_mem_groups: dict[str, dict[str, dict]] = {}


def _use_db() -> bool:
    return not get_settings().MOCK_MODE


def _loads(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return []
    return v or []


def _row(r) -> dict:
    return {"id": r[0], "key": r[1], "name": r[2], "description": r[3],
            "color": r[4] or "#00A8E0", "icon": r[5] or "",
            "track_keys": _loads(r[6]), "certification_ids": _loads(r[7]),
            "sort_order": r[8] or 0}


_COLS = "id,key,name,description,color,icon,track_keys,certification_ids,sort_order"


# ── CRUD ────────────────────────────────────────────────────────────────────
def list_groups(tenant_id: str) -> list[dict]:
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            rows = conn.execute(
                f"SELECT {_COLS} FROM groups WHERE tenant_id=%s ORDER BY sort_order, name",
                (tenant_id,)).fetchall()
        return [_row(r) for r in rows]
    return sorted(_mem_groups.get(tenant_id, {}).values(),
                  key=lambda g: (g.get("sort_order", 0), g.get("name", "")))


def get_group(tenant_id: str, key: str) -> Optional[dict]:
    key = (key or "").strip().lower()
    if not key:
        return None
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute(f"SELECT {_COLS} FROM groups WHERE tenant_id=%s AND key=%s",
                             (tenant_id, key)).fetchone()
        return _row(r) if r else None
    return _mem_groups.get(tenant_id, {}).get(key)


def create_group(tenant_id: str, key: str, name: str, description: str = "",
                 color: str = "#00A8E0", icon: str = "", track_keys: Optional[list] = None,
                 certification_ids: Optional[list] = None, sort_order: int = 0) -> dict:
    key = key.strip().lower()
    if not key or not name.strip():
        raise ValueError("key e name são obrigatórios")
    if get_group(tenant_id, key):
        raise ValueError(f"grupo '{key}' já existe")
    rec = {"id": str(uuid.uuid4()), "key": key, "name": name, "description": description,
           "color": color, "icon": icon, "track_keys": track_keys or [],
           "certification_ids": certification_ids or [], "sort_order": sort_order}
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO groups (id,tenant_id,key,name,description,color,icon,"
                "track_keys,certification_ids,sort_order) VALUES "
                "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (rec["id"], tenant_id, key, name, description, color, icon,
                 json.dumps(rec["track_keys"]), json.dumps(rec["certification_ids"]), sort_order),
            )
    else:
        _mem_groups.setdefault(tenant_id, {})[key] = rec
    logger.info(f"Grupo criado: {key} ({tenant_id[:8]})")
    return rec


def update_group(tenant_id: str, key: str, **fields) -> Optional[dict]:
    key = key.strip().lower()
    g = get_group(tenant_id, key)
    if not g:
        return None
    allowed = {"name", "description", "color", "icon", "track_keys",
               "certification_ids", "sort_order"}
    fields = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not fields:
        return g
    if _use_db():
        from app.db import get_conn
        sets, params = [], []
        for k, v in fields.items():
            sets.append(f"{k}=%s")
            params.append(json.dumps(v) if k in ("track_keys", "certification_ids") else v)
        params += [tenant_id, key]
        with get_conn() as conn:
            conn.execute(f"UPDATE groups SET {', '.join(sets)} WHERE tenant_id=%s AND key=%s", params)
    else:
        _mem_groups.get(tenant_id, {}).get(key, {}).update(fields)
    return get_group(tenant_id, key)


def delete_group(tenant_id: str, key: str) -> None:
    key = key.strip().lower()
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            # desvincula usuários do grupo antes de removê-lo
            conn.execute("UPDATE users SET group_key=NULL WHERE tenant_id=%s AND group_key=%s",
                         (tenant_id, key))
            conn.execute("DELETE FROM groups WHERE tenant_id=%s AND key=%s", (tenant_id, key))
    else:
        _mem_groups.get(tenant_id, {}).pop(key, None)


# ── Vínculo usuário ↔ grupo ───────────────────────────────────────────────────
def set_user_group(tenant_id: str, email: str, group_key: Optional[str]) -> None:
    email = email.lower()
    gk = (group_key or "").strip().lower() or None
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute("UPDATE users SET group_key=%s WHERE tenant_id=%s AND email=%s",
                         (gk, tenant_id, email))


def set_user_group_bulk(tenant_id: str, emails: list[str], group_key: Optional[str]) -> int:
    """Atribui `group_key` a vários usuários em UMA transação. Retorna nº atualizados."""
    gk = (group_key or "").strip().lower() or None
    emails = list({(e or "").lower() for e in emails if e})
    if not emails:
        return 0
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            cur = conn.execute(
                "UPDATE users SET group_key=%s WHERE tenant_id=%s AND email = ANY(%s)",
                (gk, tenant_id, emails))
            rc = cur.rowcount
            return rc if rc is not None and rc >= 0 else len(emails)
    return 0


def set_user_extra_tracks(tenant_id: str, email: str, track_keys: list) -> None:
    email = email.lower()
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute("UPDATE users SET extra_track_keys=%s WHERE tenant_id=%s AND email=%s",
                         (json.dumps(track_keys or []), tenant_id, email))


def get_user_membership(tenant_id: str, email: str) -> dict:
    """Devolve {group_key, extra_track_keys} do usuário."""
    email = email.lower()
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute("SELECT group_key, extra_track_keys FROM users "
                             "WHERE tenant_id=%s AND email=%s", (tenant_id, email)).fetchone()
        if not r:
            return {"group_key": None, "extra_track_keys": []}
        return {"group_key": r[0], "extra_track_keys": _loads(r[1])}
    return {"group_key": None, "extra_track_keys": []}


# ── Resolvedor central ────────────────────────────────────────────────────────
def _all_tracks(tenant_id: str) -> list[dict]:
    t = tenants_svc.get_tenant_by_id(tenant_id)
    if not t:
        return []
    return (tenants_svc.get_routes(t["slug"]) or {}).get("routes", [])


def visible_tracks_for_user(tenant_id: str, email: str, is_admin: bool = False) -> dict:
    """Trilhas + simulados visíveis para o usuário, segundo seu grupo/personalização.

    Admin vê tudo. Sem grupo (ou grupo sem track_keys) → todas as trilhas."""
    tracks = _all_tracks(tenant_id)
    by_key = {t.get("key"): t for t in tracks if t.get("key")}
    membership = get_user_membership(tenant_id, email)
    group = get_group(tenant_id, membership["group_key"]) if membership["group_key"] else None

    if is_admin or not group or not group.get("track_keys"):
        visible = tracks
    else:
        wanted = list(dict.fromkeys(
            list(group["track_keys"]) + list(membership.get("extra_track_keys", []))))
        visible = [by_key[k] for k in wanted if k in by_key]

    # simulados visíveis
    if group and group.get("certification_ids"):
        sim_ids = list(group["certification_ids"])
    else:
        sim_ids = []
        for t in visible:
            if t.get("certification_id"):
                sim_ids.append(t["certification_id"])
            sim_ids += t.get("sim_cert_ids", []) or []
        sim_ids = list(dict.fromkeys(sim_ids))

    return {
        "group": group,
        "tracks": visible,
        "sim_cert_ids": sim_ids,
        "all_sims": is_admin or not group,   # admin/sem-grupo → todos os simulados
    }
