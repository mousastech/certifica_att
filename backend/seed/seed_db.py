"""
Cria o schema multi-tenant e popula o Postgres (Lakebase / RDS).

- Banco de questões (certifications/questions/flashcards) é GLOBAL (compartilhado).
- users/test_sessions/test_answers são escopados por tenant_id.
- Cria os tenants 'platform' (consola superadmin) e 'santander' (primeiro cliente),
  e os usuários admin/superadmin (senha em SEED_ADMIN_PASSWORD, default Certifica@2026).

Uso:  cd backend && python -m seed.seed_db
Idempotente: CREATE ... IF NOT EXISTS e ON CONFLICT DO NOTHING.
"""
import json
import logging
import os
import sys
import uuid
from pathlib import Path

# permite rodar como `python -m seed.seed_db` a partir de backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import get_conn  # noqa: E402


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("seed")

SEED = Path(__file__).resolve().parent / "seed_data.json"
ADMIN_PW = os.environ.get("SEED_ADMIN_PASSWORD", "Certifica@2026")
SUPERADMIN_EMAIL = "moises.santos@databricks.com"

DDL = """
CREATE SCHEMA IF NOT EXISTS {schema};

CREATE TABLE IF NOT EXISTS {schema}.tenants (
    id                  TEXT PRIMARY KEY,
    slug                TEXT UNIQUE NOT NULL,
    name                TEXT NOT NULL,
    primary_color       TEXT DEFAULT '#EC0000',
    logo_url            TEXT,
    pass_mark           INT DEFAULT 70,
    allow_self_register BOOLEAN DEFAULT TRUE,
    status              TEXT DEFAULT 'active',
    program             JSONB,
    routes              JSONB,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.tenant_domains (
    email_domain TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL REFERENCES {schema}.tenants(id)
);

CREATE TABLE IF NOT EXISTS {schema}.certifications (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT, level TEXT,
    description TEXT, exam_guide_url TEXT, topics JSONB, resources JSONB
);

CREATE TABLE IF NOT EXISTS {schema}.questions (
    id TEXT PRIMARY KEY,
    certification_id TEXT NOT NULL REFERENCES {schema}.certifications(id),
    topic TEXT, question_text TEXT NOT NULL,
    question_type TEXT NOT NULL DEFAULT 'multiple_choice',
    options JSONB NOT NULL, correct_answers JSONB NOT NULL,
    explanation TEXT, difficulty INT DEFAULT 3,
    is_ai_generated BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_questions_cert ON {schema}.questions(certification_id);

CREATE TABLE IF NOT EXISTS {schema}.flashcards (
    id TEXT PRIMARY KEY,
    certification_id TEXT NOT NULL REFERENCES {schema}.certifications(id),
    topic TEXT, front TEXT NOT NULL, back TEXT NOT NULL, difficulty INT DEFAULT 2
);
CREATE INDEX IF NOT EXISTS idx_flashcards_cert ON {schema}.flashcards(certification_id);

CREATE TABLE IF NOT EXISTS {schema}.users (
    tenant_id            TEXT NOT NULL REFERENCES {schema}.tenants(id),
    email                TEXT NOT NULL,
    name                 TEXT NOT NULL,
    password_hash        TEXT NOT NULL,
    is_admin             BOOLEAN DEFAULT FALSE,
    must_change_password BOOLEAN DEFAULT FALSE,
    status               TEXT DEFAULT 'active',
    area                 TEXT,
    created_at           TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, email)
);

CREATE TABLE IF NOT EXISTS {schema}.test_sessions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES {schema}.tenants(id),
    certification_id TEXT, user_email TEXT, num_questions INT, topics JSONB,
    ai_generated BOOLEAN DEFAULT FALSE, score_pct REAL, correct INT, total INT,
    passed BOOLEAN DEFAULT FALSE, repeated_questions INT DEFAULT 0,
    duration_sec REAL, created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant_user ON {schema}.test_sessions(tenant_id, user_email, created_at);

CREATE TABLE IF NOT EXISTS {schema}.test_answers (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES {schema}.tenants(id),
    session_id TEXT REFERENCES {schema}.test_sessions(id),
    question_id TEXT, topic TEXT, selected JSONB, is_correct BOOLEAN
);
CREATE INDEX IF NOT EXISTS idx_answers_session ON {schema}.test_answers(session_id);

CREATE TABLE IF NOT EXISTS {schema}.class_progress (
    tenant_id    TEXT NOT NULL REFERENCES {schema}.tenants(id),
    user_email   TEXT NOT NULL,
    class_id     TEXT NOT NULL,
    completed_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, user_email, class_id)
);

-- Log de acessos e atividades (auditoria para o admin do tenant).
CREATE TABLE IF NOT EXISTS {schema}.activity_log (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    user_email  TEXT NOT NULL,
    user_name   TEXT,
    action      TEXT NOT NULL,        -- login | logout | register | password_change | test_submit | test_start | question_generate | class_complete | ...
    detail      JSONB,                -- payload livre por ação (cert, score, etc.)
    ip          TEXT,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_activity_tenant_time ON {schema}.activity_log(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_user ON {schema}.activity_log(tenant_id, user_email, created_at DESC);

-- "Explicar meus erros" (repair): explicações geradas por IA, salvas por tentativa
-- para revisão/export posterior. Regeração de uma sessão substitui as anteriores.
CREATE TABLE IF NOT EXISTS {schema}.repair_items (
    id               TEXT PRIMARY KEY,
    tenant_id        TEXT NOT NULL,
    session_id       TEXT NOT NULL,
    user_email       TEXT,
    certification_id TEXT,
    seq              INT DEFAULT 0,
    topic            TEXT,
    question_text    TEXT,
    misconception    TEXT,
    why_correct      TEXT,
    related_question TEXT,
    created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_repair_session ON {schema}.repair_items(tenant_id, session_id, seq);

-- Convites de admin/usuário: link com token para primeiro acesso (define a senha).
-- Ao aceitar, cria o usuário no tenant e marca accepted_at (token de uso único).
CREATE TABLE IF NOT EXISTS {schema}.invites (
    token       TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES {schema}.tenants(id),
    email       TEXT NOT NULL,
    name        TEXT NOT NULL,
    is_admin    BOOLEAN DEFAULT FALSE,
    invited_by  TEXT,
    expires_at  TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_invites_tenant ON {schema}.invites(tenant_id, created_at DESC);

-- Grupos / áreas (personas): CDO, CSO, Finanças-Genie, etc. Cada grupo recebe
-- um conjunto de trilhas (track_keys) e, opcionalmente, simulados (certification_ids).
CREATE TABLE IF NOT EXISTS {schema}.groups (
    id                TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL REFERENCES {schema}.tenants(id),
    key               TEXT NOT NULL,
    name              TEXT NOT NULL,
    description       TEXT,
    color             TEXT DEFAULT '#00A8E0',
    icon              TEXT,
    track_keys        JSONB DEFAULT '[]',   -- trilhas visíveis (keys em tenants.routes)
    certification_ids JSONB DEFAULT '[]',   -- simulados visíveis; [] = derivado das trilhas
    sort_order        INT DEFAULT 0,
    created_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (tenant_id, key)
);
CREATE INDEX IF NOT EXISTS idx_groups_tenant ON {schema}.groups(tenant_id, sort_order);

-- Personalização por usuário: grupo (área) e trilhas extras específicas.
ALTER TABLE {schema}.users ADD COLUMN IF NOT EXISTS group_key TEXT;
ALTER TABLE {schema}.users ADD COLUMN IF NOT EXISTS extra_track_keys JSONB DEFAULT '[]';
"""


def _tenant(cur, schema, slug, name, color, logo, allow_reg=True):
    cur.execute(f"SELECT id FROM {schema}.tenants WHERE slug=%s", (slug,))
    r = cur.fetchone()
    if r:
        return r[0]
    tid = str(uuid.uuid4())
    cur.execute(
        f"INSERT INTO {schema}.tenants (id,slug,name,primary_color,logo_url,allow_self_register) "
        "VALUES (%s,%s,%s,%s,%s,%s)", (tid, slug, name, color, logo, allow_reg),
    )
    return tid


def _user(cur, schema, tid, email, name, is_admin):
    cur.execute(
        f"INSERT INTO {schema}.users (tenant_id,email,name,password_hash,is_admin) "
        "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,email) DO NOTHING",
        (tid, email.lower(), name, hash_password(ADMIN_PW), is_admin),
    )


def ensure_schema():
    """Aplica só o DDL (CREATE ... IF NOT EXISTS) — idempotente e barato.

    Roda em TODO startup para que novas tabelas/índices apareçam sem depender de
    SEED_ON_STARTUP (que também popularia dados). Não escreve nenhum dado."""
    s = get_settings()
    with get_conn() as conn:
        conn.execute(DDL.format(schema=s.PGSCHEMA))
    log.info(f"Schema '{s.PGSCHEMA}' garantido (DDL idempotente).")


def run_seed():
    """Cria schema/tabelas e popula o Postgres. Idempotente.

    Reutilizável a partir do CLI (`python -m seed.seed_db`) ou do startup do
    app (SEED_ON_STARTUP=true), já que localmente não há como instalar as
    dependências (psycopg/bcrypt) fora do runtime do Databricks App.
    """
    s = get_settings()
    data = json.loads(SEED.read_text(encoding="utf-8"))
    certs, questions, flashcards = data["certifications"], data["questions"], data["flashcards"]
    schema = s.PGSCHEMA

    with get_conn() as conn:
        log.info(f"Criando schema/tabelas multi-tenant em '{schema}'...")
        conn.execute(DDL.format(schema=schema))

        with conn.cursor() as cur:
            # ── Banco GLOBAL (compartilhado por todos os tenants) ──────────────
            for c in certs:
                cur.execute(
                    f"INSERT INTO {schema}.certifications "
                    "(id,name,type,level,description,exam_guide_url,topics,resources) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO UPDATE SET "
                    "name=EXCLUDED.name, topics=EXCLUDED.topics, resources=EXCLUDED.resources",
                    (c["id"], c["name"], c.get("type"), c.get("level"), c.get("description"),
                     c.get("exam_guide_url"), json.dumps(c.get("topics", [])),
                     json.dumps(c.get("resources", []))),
                )
            for q in questions:
                cur.execute(
                    f"INSERT INTO {schema}.questions (id,certification_id,topic,question_text,"
                    "question_type,options,correct_answers,explanation,difficulty,is_ai_generated) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (q["id"], q["certification_id"], q.get("topic"), q["question_text"],
                     q.get("question_type", "multiple_choice"), json.dumps(q["options"]),
                     json.dumps(q["correct_answers"]), q.get("explanation", ""),
                     q.get("difficulty", 3), q.get("is_ai_generated", False)),
                )
            for f in flashcards:
                cur.execute(
                    f"INSERT INTO {schema}.flashcards (id,certification_id,topic,front,back,difficulty) "
                    "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (f["id"], f["certification_id"], f.get("topic"), f["front"], f["back"],
                     f.get("difficulty", 2)),
                )
            log.info(f"  banco global: {len(certs)} certs / {len(questions)} q / {len(flashcards)} fc")

            # ── Tenant único AT&T ──────────────────────────────────────────────
            att = _tenant(cur, schema, "att", "AT&T Certifica", "#00A8E0",
                          "/att-logo.svg", allow_reg=False)
            _user(cur, schema, att, SUPERADMIN_EMAIL, "Moisés Santos", is_admin=True)
            log.info(f"  tenant único: att={att[:8]}")
            log.info(f"  admin {SUPERADMIN_EMAIL} (senha: {ADMIN_PW})")

            # ── Trilhas + grupos AT&T ──────────────────────────────────────────
            seed_att_tracks_and_groups(cur, schema, att)

    log.info("Seed AT&T concluído.")


def seed_att_tracks_and_groups(cur, schema, tenant_id):
    """Semeia as trilhas (routes do tenant) e os grupos/áreas da AT&T.

    Idempotente: só grava trilhas se o tenant ainda não tiver, e usa ON CONFLICT
    nos grupos. Não sobrescreve customizações feitas pelo admin em runtime."""
    from seed.att_content import ATT_TRACKS, ATT_GROUPS

    # trilhas → tenants.routes (só se ainda vazio, para não pisar customizações)
    cur.execute(f"SELECT routes FROM {schema}.tenants WHERE id=%s", (tenant_id,))
    row = cur.fetchone()
    existing = row[0] if row else None
    if not existing:
        cur.execute(f"UPDATE {schema}.tenants SET routes=%s WHERE id=%s",
                    (json.dumps({"routes": ATT_TRACKS}), tenant_id))
        log.info(f"  trilhas semeadas: {len(ATT_TRACKS)}")

    # grupos
    for g in ATT_GROUPS:
        cur.execute(
            f"INSERT INTO {schema}.groups "
            "(id,tenant_id,key,name,description,color,icon,track_keys,certification_ids,sort_order) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT (tenant_id,key) DO NOTHING",
            (str(uuid.uuid4()), tenant_id, g["key"], g["name"], g.get("description"),
             g.get("color", "#00A8E0"), g.get("icon"),
             json.dumps(g.get("track_keys", [])),
             json.dumps(g.get("certification_ids", [])),
             g.get("sort_order", 0)),
        )
    log.info(f"  grupos semeados: {len(ATT_GROUPS)}")


def refresh_att_content():
    """FORÇA a atualização do catálogo (trilhas + grupos) do tenant 'att' a partir
    de seed/att_content.py, sobrescrevendo tenants.routes e re-sincronizando os
    grupos (ON CONFLICT DO UPDATE). Diferente do seed normal, que preserva
    customizações. Acionada por REFRESH_ATT_CONTENT=true no boot; desligar depois."""
    from seed.att_content import ATT_TRACKS, ATT_GROUPS
    s = get_settings()
    schema = s.PGSCHEMA
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT id FROM {schema}.tenants WHERE slug=%s", ("att",))
            row = cur.fetchone()
            if not row:
                log.warning("REFRESH_ATT_CONTENT: tenant 'att' não encontrado — pulando.")
                return
            tenant_id = row[0]

            # trilhas → sobrescreve
            cur.execute(f"UPDATE {schema}.tenants SET routes=%s WHERE id=%s",
                        (json.dumps({"routes": ATT_TRACKS}), tenant_id))

            # grupos → upsert (atualiza nome/descrição/cores/trilhas/ordem)
            for g in ATT_GROUPS:
                cur.execute(
                    f"INSERT INTO {schema}.groups "
                    "(id,tenant_id,key,name,description,color,icon,track_keys,certification_ids,sort_order) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (tenant_id,key) DO UPDATE SET "
                    "name=EXCLUDED.name, description=EXCLUDED.description, color=EXCLUDED.color, "
                    "icon=EXCLUDED.icon, track_keys=EXCLUDED.track_keys, sort_order=EXCLUDED.sort_order",
                    (str(uuid.uuid4()), tenant_id, g["key"], g["name"], g.get("description"),
                     g.get("color", "#00A8E0"), g.get("icon"),
                     json.dumps(g.get("track_keys", [])),
                     json.dumps(g.get("certification_ids", [])),
                     g.get("sort_order", 0)),
                )
    log.info(f"REFRESH_ATT_CONTENT: {len(ATT_TRACKS)} trilhas e {len(ATT_GROUPS)} grupos "
             "sincronizados a partir de att_content.py.")


def main():
    if get_settings().MOCK_MODE:
        log.error("MOCK_MODE=true — configure o .env para o Postgres antes de semear.")
        sys.exit(1)
    run_seed()


if __name__ == "__main__":
    main()
