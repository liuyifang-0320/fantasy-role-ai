import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.script_intelligence import (
    LLMAnalyzeRequest,
    LLMAnalyzeResponse,
    ScriptIntelligenceConfirmRequest,
    ScriptIntelligenceConfirmResponse,
    ScriptIntelligenceResultResponse,
    ScriptIntelligenceStatusResponse,
)
from app.services.access_control import ensure_user_can_access_project
from app.services.auth import get_current_user
from app.services.llm_script_understanding import (
    confirm_script_intelligence,
    get_analysis_result,
    get_latest_analysis_job,
    run_llm_script_understanding,
)
from app.services.projects import get_project


router = APIRouter()


@router.post("/{project_id}/script-intelligence/llm-analyze", response_model=LLMAnalyzeResponse)
def analyze_project_script_with_llm(
    project_id: str,
    payload: LLMAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LLMAnalyzeResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    result = run_llm_script_understanding(
        db,
        project_id=project_id,
        user_id=current_user.user_id if project.user_id else None,
        options=payload.model_dump(),
    )
    db.commit()
    return LLMAnalyzeResponse(
        analysis_id=str(result["analysis_id"]),
        status=str(result["status"]),
        summary=result,
    )


@router.get("/{project_id}/script-intelligence/status", response_model=ScriptIntelligenceStatusResponse)
def get_script_intelligence_status(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScriptIntelligenceStatusResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    job = get_latest_analysis_job(
        db,
        project_id=project_id,
        user_id=current_user.user_id if project.user_id else None,
    )
    if not job:
        return ScriptIntelligenceStatusResponse()
    return ScriptIntelligenceStatusResponse(
        analysis_id=job.analysis_id,
        status=job.status,
        provider=job.provider,
        model=job.model,
        documents_count=job.documents_count,
        chunks_count=job.chunks_count,
        characters_count=job.characters_count,
        relationships_count=job.relationships_count,
        warnings=parse_json_list(job.warnings),
    )


@router.get("/{project_id}/script-intelligence/result", response_model=ScriptIntelligenceResultResponse)
def get_script_intelligence_result(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScriptIntelligenceResultResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    job = get_latest_analysis_job(
        db,
        project_id=project_id,
        user_id=current_user.user_id if project.user_id else None,
    )
    if not job:
        return ScriptIntelligenceResultResponse()
    return ScriptIntelligenceResultResponse(
        analysis_id=job.analysis_id,
        status=job.status,
        result=get_analysis_result(job),
    )


@router.post("/{project_id}/script-intelligence/confirm", response_model=ScriptIntelligenceConfirmResponse)
def confirm_project_script_intelligence(
    project_id: str,
    payload: ScriptIntelligenceConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScriptIntelligenceConfirmResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    result = confirm_script_intelligence(
        db,
        project_id=project_id,
        user_id=current_user.user_id if project.user_id else None,
        payload=payload.model_dump(),
    )
    db.commit()
    return ScriptIntelligenceConfirmResponse(**result)


def parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [item.strip() for item in value.split(",") if item.strip()]
    return parsed if isinstance(parsed, list) else []
