"""
Información oficial de cada certificación (de la Guía de Certificación Databricks).
Datos globales (no por tenant): formato del examen + temario con ponderaciones.
"""
from typing import Optional

_GUIDE = {
    "data_engineer_associate": "https://www.databricks.com/sites/default/files/2026-05/databricks-certified-data-engineer-associate-exam-guide-may-2026-000.pdf",
    "machine_learning_associate": "https://www.databricks.com/sites/default/files/2025-02/databricks-certified-machine-learning-associate-exam-guide-1-mar-2025.pdf",
    "data_analyst_associate": "https://www.databricks.com/sites/default/files/2025-10/databricks-certified-data-analyst-associate-oct-2025.pdf",
}

CERT_INFO = {
    "data_engineer_associate": {
        "questions": "45", "duration": "90 min", "format": "Opción múltiple · proctored (online o centro)",
        "language": "EN · JP · PT-BR · KR", "validity": "2 años", "experience": "Hands-on con las tareas del exam guide",
        "exam_guide_url": _GUIDE["data_engineer_associate"],
        "domains": [
            {"name": "Data Intelligence Platform y workspace", "weight": None},
            {"name": "Ingesta y carga (Lakeflow Connect, Auto Loader, COPY INTO)", "weight": None},
            {"name": "Transformación y modelado (PySpark, SQL)", "weight": None},
            {"name": "Lakeflow Declarative Pipelines + Lakeflow Jobs (CI/CD)", "weight": None},
            {"name": "Delta Lake (ACID, time travel, MERGE, OPTIMIZE/VACUUM)", "weight": None},
            {"name": "Unity Catalog (gobierno, permisos, linaje)", "weight": None},
            {"name": "Troubleshooting, monitoreo y optimización", "weight": None},
        ],
    },
    "machine_learning_associate": {
        "questions": "48", "duration": "90 min", "format": "Opción múltiple · proctored",
        "language": "EN · JP · PT-BR · KR", "validity": "2 años", "experience": "6+ meses de ML en Databricks",
        "exam_guide_url": _GUIDE["machine_learning_associate"],
        "domains": [
            {"name": "Databricks Machine Learning", "weight": 38},
            {"name": "Model Development", "weight": 31},
            {"name": "ML Workflows", "weight": 19},
            {"name": "Model Deployment", "weight": 12},
        ],
    },
    "data_analyst_associate": {
        "questions": "45", "duration": "90 min", "format": "Opción múltiple · proctored",
        "language": "EN (solo inglés)", "validity": "2 años", "experience": "6+ meses de análisis de datos",
        "exam_guide_url": _GUIDE["data_analyst_associate"],
        "domains": [
            {"name": "Ejecución de consultas con Databricks SQL y Warehouses", "weight": 20},
            {"name": "Creación de dashboards y visualizaciones", "weight": 16},
            {"name": "Análisis de consultas", "weight": 15},
            {"name": "Desarrollo y mantenimiento de AI/BI Genie spaces", "weight": 12},
            {"name": "Entender el Data Intelligence Platform", "weight": 11},
            {"name": "Gestión de datos", "weight": 8},
            {"name": "Seguridad de datos", "weight": 8},
            {"name": "Importación de datos", "weight": 5},
            {"name": "Modelado de datos con Databricks SQL", "weight": 5},
        ],
    },
    "generative_ai_engineer_associate": {
        "questions": "45", "duration": "90 min", "format": "Opción múltiple · proctored",
        "language": "EN · JP · PT-BR · KR", "validity": "2 años", "experience": "6+ meses de GenAI/LLM en Databricks",
        "exam_guide_url": "https://www.databricks.com/sites/default/files/2026-03/Databricks-Certified-Generative-AI-Engineer-Associate-Exam-Guide-Mar26.pdf",
        "domains": [
            {"name": "Application Development", "weight": 30},
            {"name": "Assembling and Deploying Apps", "weight": 22},
            {"name": "Design Applications", "weight": 14},
            {"name": "Data Preparation", "weight": 14},
            {"name": "Evaluation and Monitoring", "weight": 12},
            {"name": "Governance", "weight": 8},
        ],
    },
    "machine_learning_professional": {
        "questions": "60", "duration": "120 min", "format": "Opción múltiple · proctored",
        "language": "EN (solo inglés)", "validity": "2 años", "experience": "1+ año de ML en producción en Databricks",
        "exam_guide_url": "https://www.databricks.com/learn/certification/machine-learning-professional",
        "domains": [
            {"name": "Experimentation", "weight": 30},
            {"name": "Model Lifecycle Management", "weight": 30},
            {"name": "Model Deployment", "weight": 25},
            {"name": "Solution and Data Monitoring", "weight": 15},
        ],
    },
    "data_engineer_professional": {
        "questions": "60", "duration": "120 min", "format": "Opción múltiple · proctored",
        "language": "EN (solo inglés)", "validity": "2 años", "experience": "1+ año de data engineering en Databricks",
        "exam_guide_url": "https://www.databricks.com/learn/certification/data-engineer-professional",
        "domains": [
            {"name": "Databricks Tooling", "weight": 20},
            {"name": "Data Processing", "weight": 30},
            {"name": "Data Modeling", "weight": 20},
            {"name": "Security and Governance", "weight": 10},
            {"name": "Monitoring and Logging", "weight": 10},
            {"name": "Testing and Deployment", "weight": 10},
        ],
    },
}


def get_cert_info(certification_id: str) -> Optional[dict]:
    return CERT_INFO.get(certification_id)
