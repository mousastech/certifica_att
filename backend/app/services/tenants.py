"""
CRUD de tenants (clientes) — multi-tenant row-level.

Cada cliente é um tenant com branding próprio (cor, logo, nome) e usuários/resultados
isolados por tenant_id. O banco de questões é GLOBAL (compartilhado entre todos).
Em MOCK_MODE usa dict em memória; em produção, o Postgres.
"""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

_mem_tenants: dict[str, dict] = {}        # slug -> tenant
_mem_domains: dict[str, str] = {}         # email_domain -> tenant_id


def _use_db() -> bool:
    return not get_settings().MOCK_MODE


def _row(r) -> dict:
    return {
        "id": r[0], "slug": r[1], "name": r[2], "primary_color": r[3],
        "logo_url": r[4], "pass_mark": r[5], "allow_self_register": r[6],
        "status": r[7], "created_at": r[8].isoformat() if r[8] else None,
    }

_COLS = "id,slug,name,primary_color,logo_url,pass_mark,allow_self_register,status,created_at"


def get_tenant_by_slug(slug: str) -> Optional[dict]:
    slug = (slug or "").strip().lower()
    if not slug:
        return None
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute(f"SELECT {_COLS} FROM tenants WHERE slug=%s", (slug,)).fetchone()
        return _row(r) if r else None
    return _mem_tenants.get(slug)


def get_tenant_by_id(tenant_id: str) -> Optional[dict]:
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute(f"SELECT {_COLS} FROM tenants WHERE id=%s", (tenant_id,)).fetchone()
        return _row(r) if r else None
    return next((t for t in _mem_tenants.values() if t["id"] == tenant_id), None)


def resolve_slug(query: str) -> Optional[str]:
    """Resuelve un tenant activo por slug exacto o por nombre (case-insensitive)."""
    q = (query or "").strip().lower()
    if not q:
        return None
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute(
                "SELECT slug FROM tenants WHERE status='active' AND "
                "(lower(slug)=%s OR lower(name)=%s) ORDER BY (lower(slug)=%s) DESC LIMIT 1",
                (q, q, q),
            ).fetchone()
        return r[0] if r else None
    for t in _mem_tenants.values():
        if t["slug"].lower() == q or t["name"].lower() == q:
            return t["slug"]
    return None


def tenant_id_for_domain(domain: str) -> Optional[str]:
    domain = (domain or "").strip().lower()
    if not domain:
        return None
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute("SELECT tenant_id FROM tenant_domains WHERE email_domain=%s",
                             (domain,)).fetchone()
        return r[0] if r else None
    return _mem_domains.get(domain)


def create_tenant(slug: str, name: str, primary_color: str = "#EC0000",
                  logo_url: Optional[str] = None, pass_mark: int = 70,
                  allow_self_register: bool = True,
                  email_domain: Optional[str] = None) -> dict:
    slug = slug.strip().lower()
    if get_tenant_by_slug(slug):
        raise ValueError(f"slug '{slug}' já existe")
    tid = str(uuid.uuid4())
    rec = {"id": tid, "slug": slug, "name": name, "primary_color": primary_color,
           "logo_url": logo_url, "pass_mark": pass_mark,
           "allow_self_register": allow_self_register, "status": "active",
           "created_at": None}
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO tenants (id,slug,name,primary_color,logo_url,pass_mark,"
                "allow_self_register,status) VALUES (%s,%s,%s,%s,%s,%s,%s,'active')",
                (tid, slug, name, primary_color, logo_url, pass_mark, allow_self_register),
            )
            if email_domain:
                conn.execute("INSERT INTO tenant_domains (email_domain,tenant_id) "
                             "VALUES (%s,%s) ON CONFLICT (email_domain) DO NOTHING",
                             (email_domain.strip().lower(), tid))
    else:
        _mem_tenants[slug] = rec
        if email_domain:
            _mem_domains[email_domain.strip().lower()] = tid
    logger.info(f"Tenant criado: {slug} ({tid})")
    return rec


def default_program(name: str) -> dict:
    """Programa por defecto (genérico) si el tenant no lo personalizó."""
    return {
        "title": f"Programa de Certificación {name}",
        "tagline": "Impulsa tu talento. Transforma tu futuro.",
        "intro": "Un recorrido guiado para prepararte y obtener tu certificación Databricks: "
                 "estudia, practica con simulacros y flashcards, y llega listo al examen oficial.",
        "kpis": [],
        "pillars": [
            {"title": "Ruta personalizada", "desc": "Elegí tu certificación objetivo y avanzá a tu ritmo.", "link": None},
            {"title": "Práctica con IA", "desc": "Simulacros con corrección, explicaciones y flashcards.", "link": None},
            {"title": "Seguimiento", "desc": "Tu progreso y resultados quedan registrados.", "link": None},
            {"title": "Reconocimiento", "desc": "Llegá al examen oficial con confianza.", "link": None},
        ],
        "roadmap": [
            {"title": "Aprender", "desc": "Elegí tu ruta y mirá las clases para prepararte.", "link": "/rutas"},
            {"title": "Practicar", "desc": "Simulacros y flashcards en esta plataforma.", "link": "/simulacros"},
            {"title": "Certificar", "desc": "Registro de exámenes (proctored): plataforma Webassessor.", "link": "https://www.webassessor.com/databricks"},
            {"title": "Impacto", "desc": "Aplicá lo aprendido en proyectos reales.", "link": None},
        ],
        "exam_intro": ("Examen oficial proctored · opción múltiple · 90 min · ~45 preguntas (48 en ML) · "
                       "aprobación con scaled scoring (histórico ~70%; meta ≥80% en simulacros) · vigencia 2 años · "
                       "idiomas EN/PT-BR/JP/KR (Data Analyst solo EN). Paso 0 obligatorio: completar la encuesta LNA de diagnóstico."),
        "exam_steps": [
            {"title": "1. Registro", "desc": "Creá tu cuenta en Webassessor y seleccioná el examen.", "link": "https://www.webassessor.com/databricks"},
            {"title": "2. Modalidad", "desc": "Online proctored (desde casa/oficina con webcam) o en centro de pruebas.", "link": None},
            {"title": "3. Requisitos (online)", "desc": "Equipo con cámara y micrófono, conexión estable, espacio despejado, documento de identidad válido. Instalá el software de proctoring (Sentinel) antes.", "link": None},
            {"title": "4. Durante el examen", "desc": "Sin material de apoyo · 90 minutos · opción múltiple.", "link": None},
            {"title": "5. Resultado", "desc": "Inmediato al finalizar. Tu badge aparece en credentials.databricks.com.", "link": "https://credentials.databricks.com/"},
            {"title": "6. Reintento", "desc": "Si no aprobás, hay un periodo de espera antes de reintentar (consultá las políticas vigentes en Webassessor).", "link": None},
        ],
        "resources": [
            {"label": "Registro de exámenes — Webassessor", "url": "https://www.webassessor.com/databricks"},
            {"label": "Mis credenciales / badges", "url": "https://credentials.databricks.com/"},
            {"label": "Encuesta de diagnóstico (LNA)", "url": "https://surveys.training.databricks.com/jfe/form/SV_8doSEwq0YbjWvVI?org_id=0013f00000Ai2CDAAZ&show_individual_results=Yes"},
            {"label": "Overview de certificaciones Databricks", "url": "https://www.databricks.com/learn/certification"},
        ],
        "ranking_enabled": False, "ranking_intro": "", "ranking_tiers": [],
    }


_ACADEMY = "https://customer-academy.databricks.com/"   # portal de eLearning self-paced

# Rutas oficiales (réplica del programa Data Champions): 3 rutas, cursos por nivel.
# (title, level, duración). level: fundamentos | associate | professional.
_OFFICIAL_ROUTES = [
    ('Ingeniería de Datos',
     'Pipelines, ingesta y procesamiento a gran escala (Lakeflow, Spark, Delta Lake), gobierno, performance y CI/CD.',
     'data_engineer_associate', [
        ('Databricks Fundamentals', 'fundamentos', '3h', 'https://www.databricks.com/br/training/catalog/databricks-fundamentals-portuguese-br-2299'),
        ('Get Started with Databricks for Data Engineering', 'fundamentos', '2h', 'https://www.databricks.com/es/training/catalog/get-started-with-databricks-for-data-engineering-spanish-3908'),
        ('Databricks Fundamentals Accreditation', 'fundamentos', '3h', 'https://customer-academy.databricks.com/learn/courses/2308/databricks-fundamentals-accreditation'),
        ('Data Ingestion with Delta Lake', 'associate', '4h', 'https://www.databricks.com/br/training/catalog/data-ingestion-with-delta-lake-portuguese-br-3301'),
        ('Deploy Workloads with Lakeflow Jobs', 'associate', '4h', 'https://www.databricks.com/br/training/catalog/deploy-workloads-with-lakeflow-jobs-portuguese-br-3278'),
        ('Build Data Pipelines with Lakeflow Declarative Pipelines', 'associate', '4h', 'https://www.databricks.com/br/training/catalog/build-data-pipelines-with-lakeflow-declarative-pipelines-portuguese-br-3289'),
        ('DevOps Essentials for Data Engineering', 'associate', '2h', 'https://www.databricks.com/br/training/catalog/devops-essentials-for-data-engineering-portuguese-br-3923'),
        ('Databricks Streaming and Lakeflow Spark Declarative Pipelines', 'professional', '4h', 'https://www.databricks.com/br/training/catalog/databricks-streaming-and-lakeflow-spark-declarative-pipelines-portuguese-br-3083'),
        ('Databricks Data Privacy', 'professional', '2h', 'https://www.databricks.com/br/training/catalog/databricks-data-privacy-portuguese-br-4012'),
        ('Databricks Performance Optimization', 'professional', '2h', 'https://www.databricks.com/br/training/catalog/databricks-performance-optimization-portuguese-br-3080'),
     ]),
    ('Ciencia de Datos & IA',
     'Machine Learning, MLOps, IA Generativa, Agent Bricks, Mosaic AI y agentes inteligentes en Databricks.',
     'machine_learning_associate', [
        ('Databricks Fundamentals', 'fundamentos', '3h', 'https://www.databricks.com/br/training/catalog/databricks-fundamentals-portuguese-br-2299'),
        ('Get Started with Databricks for Machine Learning', 'fundamentos', '2h', 'https://www.databricks.com/br/training/catalog/get-started-with-databricks-for-machine-learning-portuguese-br-3578'),
        ('Databricks Fundamentals Accreditation', 'fundamentos', '3h', 'https://customer-academy.databricks.com/learn/courses/2308/databricks-fundamentals-accreditation'),
        ('AI Agent Fundamentals', 'fundamentos', '1.5h', 'https://www.databricks.com/br/training/catalog/ai-agent-fundamentals-portuguese-br-4742'),
        ('Generative AI Fundamentals', 'fundamentos', '1.5h', 'https://www.databricks.com/br/training/catalog/generative-ai-fundamentals-portuguese-br-2252'),
        ('Data Modeling Strategies', 'associate', '2h', 'https://www.databricks.com/br/training/catalog/data-modeling-strategies-portuguese-br-4266'),
        ('Data Preparation for Machine Learning', 'associate', '2h', 'https://customer-academy.databricks.com/learn/courses/2343/data-preparation-for-machine-learning'),
        ('Machine Learning Model Development', 'associate', '2h', 'https://customer-academy.databricks.com/learn/courses/2390/machine-learning-model-development'),
        ('Advanced Machine Learning Operations', 'professional', '2h', 'https://customer-academy.databricks.com/learn/courses/3508/advanced-machine-learning-operations'),
     ]),
    ('Analista de Datos',
     'SQL Analytics, AI/BI Dashboards, Genie, Data Warehousing, self-service y visualización en el Lakehouse.',
     'data_analyst_associate', [
        ('Databricks Fundamentals', 'fundamentos', '3h', 'https://www.databricks.com/br/training/catalog/databricks-fundamentals-portuguese-br-2299'),
        ('Get Started with SQL Analytics and BI on Databricks', 'fundamentos', '2h', 'https://www.databricks.com/es/training/catalog/get-started-with-sql-analytics-and-bi-on-databricks-spanish-3728'),
        ('Databricks Fundamentals Accreditation', 'fundamentos', '3h', 'https://customer-academy.databricks.com/learn/courses/2308/databricks-fundamentals-accreditation'),
        ('Get Started with Databricks for Data Warehousing', 'associate', '2h', 'https://www.databricks.com/training/catalog/get-started-with-databricks-for-data-warehousing-3603'),
        ('Databricks AI/BI for Self-Service Analytics', 'associate', '3h', 'https://www.databricks.com/br/training/catalog/databricks-aibi-for-self-service-analytics-portuguese-br-3694'),
        ('AI/BI for Data Analysts', 'associate', '2h', 'https://www.databricks.com/br/training/catalog/aibi-for-data-analysts-portuguese-br-4195'),
        ('Data Warehousing with Databricks', 'professional', '2h', 'https://www.databricks.com/br/training/catalog/data-warehousing-with-databricks-portuguese-br-4230'),
        ('SQL Analytics on Databricks', 'professional', '2h', 'https://www.databricks.com/br/training/catalog/sql-analytics-on-databricks-portuguese-br-4207'),
     ]),
]


def default_routes() -> dict:
    routes = []
    for ri, (name, desc, cert, classes) in enumerate(_OFFICIAL_ROUTES):
        cl = [{"id": f"r{ri}-c{ci}", "title": ti, "desc": "", "type": "elearning",
               "level": lv, "duration": du, "free": True, "url": url}
              for ci, (ti, lv, du, url) in enumerate(classes)]
        routes.append({"name": name, "description": desc, "certification_id": cert, "classes": cl})
    return {"routes": routes}


def get_routes(slug: str) -> dict:
    t = get_tenant_by_slug(slug)
    if not t:
        return {"routes": []}
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute("SELECT routes FROM tenants WHERE slug=%s", (slug,)).fetchone()
        rt = r[0] if r and r[0] else None
        if isinstance(rt, str):
            import json as _j; rt = _j.loads(rt)
        return rt or default_routes()
    return t.get("_routes") or default_routes()


def set_routes(slug: str, routes: dict) -> None:
    slug = slug.strip().lower()
    if _use_db():
        import json as _j
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute("UPDATE tenants SET routes=%s WHERE slug=%s", (_j.dumps(routes), slug))
    elif slug in _mem_tenants:
        _mem_tenants[slug]["_routes"] = routes


def get_program(slug: str) -> dict:
    t = get_tenant_by_slug(slug)
    if not t:
        return default_program("")
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            r = conn.execute("SELECT program FROM tenants WHERE slug=%s", (slug,)).fetchone()
        prog = r[0] if r and r[0] else None
        if isinstance(prog, str):
            import json as _j; prog = _j.loads(prog)
        return prog or default_program(t["name"])
    return t.get("_program") or default_program(t["name"])


def set_program(slug: str, program: dict) -> None:
    slug = slug.strip().lower()
    if _use_db():
        import json as _j
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute("UPDATE tenants SET program=%s WHERE slug=%s", (_j.dumps(program), slug))
    elif slug in _mem_tenants:
        _mem_tenants[slug]["_program"] = program


def update_branding(slug: str, name: Optional[str] = None,
                    primary_color: Optional[str] = None,
                    logo_url: Optional[str] = None) -> None:
    slug = slug.strip().lower()
    fields = {"name": name, "primary_color": primary_color, "logo_url": logo_url}
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields:
        return
    if _use_db():
        from app.db import get_conn
        sets = ", ".join(f"{k}=%s" for k in fields)
        with get_conn() as conn:
            conn.execute(f"UPDATE tenants SET {sets} WHERE slug=%s", [*fields.values(), slug])
    elif slug in _mem_tenants:
        _mem_tenants[slug].update(fields)


def set_status(slug: str, status: str) -> None:
    slug = slug.strip().lower()
    if _use_db():
        from app.db import get_conn
        with get_conn() as conn:
            conn.execute("UPDATE tenants SET status=%s WHERE slug=%s", (status, slug))
    elif slug in _mem_tenants:
        _mem_tenants[slug]["status"] = status


def list_tenants() -> List[dict]:
    if not _use_db():
        return list(_mem_tenants.values())
    from app.db import get_conn
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT t.id,t.slug,t.name,t.primary_color,t.logo_url,t.pass_mark,"
            f"t.allow_self_register,t.status,t.created_at,"
            f"(SELECT COUNT(*) FROM users u WHERE u.tenant_id=t.id),"
            f"(SELECT COUNT(*) FROM test_sessions s WHERE s.tenant_id=t.id) "
            f"FROM tenants t ORDER BY t.created_at"
        ).fetchall()
    out = []
    for r in rows:
        d = _row(r); d["user_count"] = r[9]; d["attempt_count"] = r[10]
        out.append(d)
    return out
