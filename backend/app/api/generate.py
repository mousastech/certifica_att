"""
Endpoints de geração via LLM (Foundation Model API) — alinhados com o
"AI Prep Guide: Any Databricks Certification":
- POST /            → questões (Diagnose/Practice)
- POST /repair      → explicar erros (Step 4.5)
- POST /deep-dive   → ensinar um objetivo (Step 4.3)
- POST /hands-on/{certification_id} → checklist prático (Step 5)
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request

from app.models.schemas import (
    GenerateRequest, GenerateResponse, UserPublic,
    RepairRequest, RepairResponse, RepairItem,
    DeepDiveRequest, DeepDiveResponse,
    HandsOnResponse, HandsOnTask,
)
from app.config import get_settings
from app.auth import security
from app.services import repo, activity
from app.services.llm_gen import (
    generate_questions, repair_wrong_answers, deep_dive_objective,
    hands_on_checklist,
)

logger = logging.getLogger(__name__)

# Mensagem genérica devolvida ao cliente em falhas de LLM (o detalhe do erro fica
# só no log do servidor — não expomos stack traces / internals na resposta).
_GEN_ERR = "No fue posible generar el contenido en este momento. Intente nuevamente."


def obo_token(request: Request) -> None:
    """Captura o token do usuário (Databricks Apps OBO) para este request, de
    forma que as chamadas de LLM usem a identidade do usuário logado.

    Feito como dependency (não middleware) porque o contextvar setado aqui roda
    no mesmo contexto da task do endpoint — o BaseHTTPMiddleware do Starlette
    roda em outra task e não propagaria o valor."""
    from app.auth.workspace_client import set_user_token
    set_user_token(request.headers.get("X-Forwarded-Access-Token"))


router = APIRouter(dependencies=[Depends(obo_token)])


def _source() -> str:
    return "mock" if get_settings().MOCK_MODE else "llm"


@router.post("/", response_model=GenerateResponse)
async def generate(req: GenerateRequest, request: Request,
                   user: UserPublic = Depends(security.get_current_user)):
    cert = repo.get_certification(req.certification_id)
    if not cert:
        raise HTTPException(404, "Certificação não encontrada")
    try:
        questions = generate_questions(
            certification=cert, count=req.count,
            topics=req.topics, difficulty=req.difficulty,
        )
    except Exception as e:
        logger.error(f"Erro na geração: {e}", exc_info=True)
        return GenerateResponse(success=False, source="error", message=_GEN_ERR)

    if req.persist and questions:
        try:
            repo.add_questions(questions)
        except Exception as e:
            logger.warning(f"Não foi possível persistir questões geradas: {e}")

    activity.log_event(
        user.tenant_id, user.email, "question_generate", request=request, user_name=user.name,
        detail={"certification_id": req.certification_id, "count": len(questions),
                "topics": req.topics or []},
    )
    return GenerateResponse(success=True, questions=questions, source=_source())


@router.post("/repair", response_model=RepairResponse)
async def repair(req: RepairRequest,
                 user: UserPublic = Depends(security.get_current_user)):
    """Step 4.5 — explica cada resposta errada + questão relacionada.
    Se `session_id` vier informado, salva as explicações na tentativa (para
    revisão e export em PDF depois)."""
    cert = repo.get_certification(req.certification_id)
    if not cert:
        raise HTTPException(404, "Certificação não encontrada")
    if not req.wrong:
        return RepairResponse(success=True, items=[], source=_source())
    try:
        raw = repair_wrong_answers(cert, [w.model_dump() for w in req.wrong])
    except Exception as e:
        logger.error(f"Erro no repair: {e}", exc_info=True)
        return RepairResponse(success=False, source="error", message=_GEN_ERR)
    items = [RepairItem(**{k: v for k, v in it.items() if k in RepairItem.model_fields})
             for it in raw]
    if req.session_id and items:
        try:
            repo.save_repair_items(user.tenant_id, req.session_id, user.email,
                                   req.certification_id,
                                   [i.model_dump() for i in items])
        except Exception as e:
            logger.warning(f"Não foi possível salvar as explicações: {e}")
    return RepairResponse(success=True, items=items, source=_source())


@router.post("/deep-dive", response_model=DeepDiveResponse)
async def deep_dive(req: DeepDiveRequest,
                    _: UserPublic = Depends(security.get_current_user)):
    """Step 4.3 — ensina um objetivo específico com fontes oficiais."""
    cert = repo.get_certification(req.certification_id)
    if not cert:
        raise HTTPException(404, "Certificação não encontrada")
    if not req.objective.strip():
        raise HTTPException(422, "Objetivo obrigatório")
    try:
        d = deep_dive_objective(cert, req.objective.strip())
    except Exception as e:
        logger.error(f"Erro no deep-dive: {e}", exc_info=True)
        return DeepDiveResponse(success=False, source="error", message=_GEN_ERR)
    d = {k: v for k, v in (d or {}).items() if k in DeepDiveResponse.model_fields}
    return DeepDiveResponse(success=True, source=_source(), **d)


@router.post("/hands-on/{certification_id}", response_model=HandsOnResponse)
async def hands_on(certification_id: str,
                   _: UserPublic = Depends(security.get_current_user)):
    """Step 5 (CRÍTICO) — checklist de tarefas práticas por certificação."""
    cert = repo.get_certification(certification_id)
    if not cert:
        raise HTTPException(404, "Certificação não encontrada")
    try:
        raw = hands_on_checklist(cert)
    except Exception as e:
        logger.error(f"Erro no hands-on: {e}", exc_info=True)
        return HandsOnResponse(success=False, certification_id=certification_id,
                               source="error", message=_GEN_ERR)
    tasks = [HandsOnTask(**{k: v for k, v in t.items() if k in HandsOnTask.model_fields})
             for t in raw if t.get("task")]
    return HandsOnResponse(success=True, certification_id=certification_id,
                           tasks=tasks, source=_source())
