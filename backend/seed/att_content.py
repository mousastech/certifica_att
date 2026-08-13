"""
Conteúdo semente da AT&T — grupos (áreas/personas) e trilhas de capacitação.

A plataforma é um PLANO DE CAPACITAÇÃO CORPORATIVA em Databricks (não apenas
preparação para certificação). Uma *trilha* é um percurso curado de aprendizagem
(cursos eLearning, hands-on, docs, vídeos) com simulados OPCIONAIS. As trilhas são
atribuídas a *grupos* (áreas/personas) e podem ser personalizadas por usuário.

Editável em runtime pelo admin (telas /admin/trilhas e /admin/grupos); estes são
apenas os valores iniciais semeados no primeiro boot.
"""
from __future__ import annotations

_ACADEMY = "https://customer-academy.databricks.com/"
_CATALOG = "https://www.databricks.com/training/catalog"


def _cls(key: str, i: int, title: str, level: str, duration: str, url: str,
         ctype: str = "elearning", desc: str = "") -> dict:
    return {"id": f"{key}-c{i}", "title": title, "desc": desc, "type": ctype,
            "level": level, "duration": duration, "free": True, "url": url}


# ─────────────────────────────────────────────────────────────────────────────
# TRILHAS (percursos de capacitação). certification_id/sim_cert_ids são OPCIONAIS.
# ─────────────────────────────────────────────────────────────────────────────
ATT_TRACKS: list[dict] = [
    {
        "key": "fundamentos",
        "name": "Fundamentos Databricks",
        "description": "Base comum para toda a AT&T: plataforma Lakehouse, Unity Catalog, "
                       "notebooks e primeiros passos. Ponto de partida de todas as áreas.",
        "icon": "Compass", "color": "#00A8E0", "certification_id": None, "sim_cert_ids": [],
        "classes": [
            _cls("fundamentos", 0, "Databricks Fundamentals", "fundamentos", "3h",
                 "https://www.databricks.com/training/catalog/databricks-fundamentals-2299"),
            _cls("fundamentos", 1, "Databricks Fundamentals Accreditation", "fundamentos", "1h",
                 f"{_ACADEMY}learn/courses/2308/databricks-fundamentals-accreditation", "accreditation"),
            _cls("fundamentos", 2, "Lakehouse & Unity Catalog Overview", "fundamentos", "2h",
                 f"{_CATALOG}"),
            _cls("fundamentos", 3, "Navegando o Workspace da AT&T (hands-on)", "fundamentos", "1h",
                 "https://fevm-moi-ai.cloud.databricks.com", "hands-on",
                 "Sessão prática guiada no workspace corporativo da AT&T."),
        ],
    },
    {
        "key": "gobierno_datos",
        "name": "Gobierno de Datos & Unity Catalog",
        "description": "Governança, linhagem, políticas de acesso, qualidade e catálogo "
                       "corporativo — pilar da Oficina do CDO.",
        "icon": "ShieldCheck", "color": "#0568AE", "certification_id": None, "sim_cert_ids": [],
        "classes": [
            _cls("gobierno_datos", 0, "Data Governance with Unity Catalog", "associate", "3h",
                 f"{_CATALOG}"),
            _cls("gobierno_datos", 1, "Data Lineage & Auditing", "associate", "2h", f"{_CATALOG}"),
            _cls("gobierno_datos", 2, "Databricks Data Privacy", "professional", "2h",
                 "https://www.databricks.com/training/catalog/databricks-data-privacy-4012"),
            _cls("gobierno_datos", 3, "Política Corporativa Databricks AT&T (leitura)", "fundamentos",
                 "1h", "https://www.databricks.com/trust", "doc"),
        ],
    },
    {
        "key": "seguridad",
        "name": "Seguridad & Cumplimiento",
        "description": "Segurança da plataforma, isolamento, secrets, redes e conformidade — "
                       "trilha da área de Ciberseguridad (CSO).",
        "icon": "Lock", "color": "#009FDB", "certification_id": None, "sim_cert_ids": [],
        "classes": [
            _cls("seguridad", 0, "Databricks Security Fundamentals", "fundamentos", "2h", f"{_CATALOG}"),
            _cls("seguridad", 1, "Securing the Lakehouse (rede, secrets, tokens)", "associate", "3h",
                 f"{_CATALOG}", "elearning"),
            _cls("seguridad", 2, "Identity & Access — SCIM / AIM / OAuth", "associate", "2h",
                 f"{_CATALOG}"),
            _cls("seguridad", 3, "Auditoría con System Tables (hands-on)", "professional", "2h",
                 "https://docs.databricks.com/admin/system-tables/", "hands-on"),
        ],
    },
    {
        "key": "genie_finanzas",
        "name": "Genie para Finanças",
        "description": "Análise self-service em linguagem natural com AI/BI Genie para o time "
                       "de Finanças — perguntar aos dados sem escrever SQL.",
        "icon": "Sparkles", "color": "#00A8E0", "certification_id": None,
        "sim_cert_ids": ["data_analyst_associate"],
        "classes": [
            _cls("genie_finanzas", 0, "Get Started with AI/BI on Databricks", "fundamentos", "2h",
                 "https://www.databricks.com/training/catalog"),
            _cls("genie_finanzas", 1, "Databricks AI/BI Genie — Self-Service Analytics", "fundamentos",
                 "2h", "https://www.databricks.com/product/ai-bi", "elearning",
                 "Perguntar aos dados em linguagem natural; curar Genie Spaces."),
            _cls("genie_finanzas", 2, "AI/BI Dashboards para Finanças", "associate", "2h",
                 "https://www.databricks.com/training/catalog"),
            _cls("genie_finanzas", 3, "Genie Space de Finanças AT&T (hands-on)", "associate", "1.5h",
                 "https://fevm-moi-ai.cloud.databricks.com", "hands-on",
                 "Criar e curar um Genie Space com dados financeiros da AT&T."),
        ],
    },
    {
        "key": "ingenieria",
        "name": "Ingeniería de Datos",
        "description": "Pipelines, ingestão e processamento em escala com Lakeflow, Spark e "
                       "Delta Lake, com CI/CD e performance.",
        "icon": "Database", "color": "#0568AE",
        "certification_id": "data_engineer_associate",
        "sim_cert_ids": ["data_engineer_associate", "data_engineer_professional"],
        "classes": [
            _cls("ingenieria", 0, "Get Started with Databricks for Data Engineering", "fundamentos", "2h",
                 "https://www.databricks.com/training/catalog/get-started-with-databricks-for-data-engineering-spanish-3908"),
            _cls("ingenieria", 1, "Data Ingestion with Delta Lake", "associate", "4h",
                 "https://www.databricks.com/training/catalog/data-ingestion-with-delta-lake-3301"),
            _cls("ingenieria", 2, "Build Data Pipelines with Lakeflow Declarative Pipelines", "associate",
                 "4h", "https://www.databricks.com/training/catalog/build-data-pipelines-with-lakeflow-declarative-pipelines-3289"),
            _cls("ingenieria", 3, "Deploy Workloads with Lakeflow Jobs", "associate", "4h",
                 "https://www.databricks.com/training/catalog/deploy-workloads-with-lakeflow-jobs-3278"),
            _cls("ingenieria", 4, "Databricks Performance Optimization", "professional", "2h",
                 "https://www.databricks.com/training/catalog/databricks-performance-optimization-3080"),
        ],
    },
    {
        "key": "ciencia_datos",
        "name": "Ciencia de Datos & IA",
        "description": "Machine Learning, MLOps, IA Generativa, Mosaic AI e agentes inteligentes "
                       "sobre o Lakehouse.",
        "icon": "BrainCircuit", "color": "#009FDB",
        "certification_id": "machine_learning_associate",
        "sim_cert_ids": ["machine_learning_associate", "generative_ai_engineer_associate"],
        "classes": [
            _cls("ciencia_datos", 0, "Get Started with Databricks for Machine Learning", "fundamentos",
                 "2h", "https://www.databricks.com/training/catalog/get-started-with-databricks-for-machine-learning-3578"),
            _cls("ciencia_datos", 1, "Generative AI Fundamentals", "fundamentos", "1.5h",
                 "https://www.databricks.com/training/catalog/generative-ai-fundamentals-2252"),
            _cls("ciencia_datos", 2, "AI Agent Fundamentals", "fundamentos", "1.5h",
                 "https://www.databricks.com/training/catalog/ai-agent-fundamentals-4742"),
            _cls("ciencia_datos", 3, "Machine Learning Model Development", "associate", "2h",
                 f"{_ACADEMY}learn/courses/2390/machine-learning-model-development"),
            _cls("ciencia_datos", 4, "Advanced Machine Learning Operations", "professional", "2h",
                 f"{_ACADEMY}learn/courses/3508/advanced-machine-learning-operations"),
        ],
    },
    {
        "key": "analitica",
        "name": "Analítica & AI/BI",
        "description": "SQL Analytics, Data Warehousing, AI/BI Dashboards e visualização "
                       "self-service no Lakehouse.",
        "icon": "BarChart3", "color": "#00A8E0",
        "certification_id": "data_analyst_associate",
        "sim_cert_ids": ["data_analyst_associate"],
        "classes": [
            _cls("analitica", 0, "Get Started with SQL Analytics and BI on Databricks", "fundamentos",
                 "2h", "https://www.databricks.com/training/catalog/get-started-with-sql-analytics-and-bi-on-databricks-spanish-3728"),
            _cls("analitica", 1, "Databricks AI/BI for Self-Service Analytics", "associate", "3h",
                 "https://www.databricks.com/training/catalog/databricks-aibi-for-self-service-analytics-3694"),
            _cls("analitica", 2, "Data Warehousing with Databricks", "professional", "2h",
                 "https://www.databricks.com/training/catalog/data-warehousing-with-databricks-4230"),
            _cls("analitica", 3, "SQL Analytics on Databricks", "professional", "2h",
                 "https://www.databricks.com/training/catalog/sql-analytics-on-databricks-4207"),
        ],
    },
    {
        "key": "liderazgo",
        "name": "Databricks para Líderes",
        "description": "Visão executiva: estratégia de dados & IA, casos de uso e ROI da "
                       "plataforma — para gestores e patrocinadores.",
        "icon": "Rocket", "color": "#0568AE", "certification_id": None, "sim_cert_ids": [],
        "classes": [
            _cls("liderazgo", 0, "Databricks Fundamentals (visão de negócio)", "fundamentos", "3h",
                 "https://www.databricks.com/training/catalog/databricks-fundamentals-2299"),
            _cls("liderazgo", 1, "Data + AI Strategy para Executivos", "fundamentos", "1h",
                 "https://www.databricks.com/training/catalog", "doc"),
            _cls("liderazgo", 2, "Casos de Uso de IA na AT&T (workshop)", "fundamentos", "1h",
                 "https://www.databricks.com/customers", "hands-on"),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# GRUPOS (áreas / personas). track_keys aponta para trilhas acima.
# ─────────────────────────────────────────────────────────────────────────────
ATT_GROUPS: list[dict] = [
    {"key": "cdo", "name": "Oficina del CDO", "icon": "Building2", "color": "#00A8E0",
     "description": "Governança de dados, catálogo corporativo e estratégia de dados.",
     "track_keys": ["fundamentos", "gobierno_datos", "liderazgo"], "sort_order": 1},
    {"key": "cso", "name": "Ciberseguridad (CSO)", "icon": "Lock", "color": "#009FDB",
     "description": "Segurança, conformidade e auditoria da plataforma.",
     "track_keys": ["fundamentos", "seguridad", "gobierno_datos"], "sort_order": 2},
    {"key": "finanzas", "name": "Finanças — Genie", "icon": "Sparkles", "color": "#00A8E0",
     "description": "Análise self-service com AI/BI Genie para o time financeiro.",
     "track_keys": ["fundamentos", "genie_finanzas", "analitica"], "sort_order": 3},
    {"key": "data_eng", "name": "Ingeniería de Datos", "icon": "Database", "color": "#0568AE",
     "description": "Times de engenharia de dados e plataforma.",
     "track_keys": ["fundamentos", "ingenieria", "gobierno_datos"], "sort_order": 4},
    {"key": "data_science", "name": "Ciencia de Datos & IA", "icon": "BrainCircuit", "color": "#009FDB",
     "description": "Cientistas de dados, ML e IA Generativa.",
     "track_keys": ["fundamentos", "ciencia_datos", "genie_finanzas"], "sort_order": 5},
    {"key": "analistas", "name": "Analistas de Negócio", "icon": "BarChart3", "color": "#00A8E0",
     "description": "Analistas de BI e self-service analytics.",
     "track_keys": ["fundamentos", "analitica", "genie_finanzas"], "sort_order": 6},
    {"key": "liderazgo", "name": "Liderança & Ejecutivos", "icon": "Rocket", "color": "#0568AE",
     "description": "Gestores e patrocinadores executivos.",
     "track_keys": ["fundamentos", "liderazgo"], "sort_order": 7},
]


def att_routes_payload() -> dict:
    """Payload de trilhas (routes) para o tenant AT&T."""
    return {"routes": ATT_TRACKS}
