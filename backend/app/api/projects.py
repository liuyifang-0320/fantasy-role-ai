from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.character_candidates import serialize_candidate
from app.api.character_relationships import serialize_relationship
from app.api.characters import build_generated_character_response
from app.schemas.character import CharacterGenerateRequest
from app.schemas.character_candidate import (
    BatchGenerateFailed,
    BatchGenerateRequest,
    BatchGenerateResponse,
    BatchGenerateSkipped,
    CharacterCandidateResponse,
)
from app.schemas.character_relationship import (
    CharacterRelationshipResponse,
    RelationshipGraphResponse,
)
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdateRequest,
)
from app.services.character_candidates import (
    can_generate_candidate,
    candidate_generation_name,
    get_candidate,
    list_candidates,
    mark_candidate_generated,
    parse_json_list,
)
from app.services.character_relationships import (
    build_relationship_graph,
    extract_relationships_for_project,
    get_relationships_for_character,
    list_relationships,
    summarize_relationship_hints,
)
from app.services.characters import generate_character
from app.models import UploadedFile, User
from app.services.access_control import (
    ensure_user_can_access_candidate,
    ensure_user_can_access_project,
)
from app.services.auth import get_current_user
from app.services.projects import (
    archive_project,
    create_project,
    get_project,
    get_project_summary,
    list_projects,
    update_project,
)
from app.services.script_intelligence_pipeline import run_script_intelligence_pipeline


router = APIRouter()


def serialize_project(project, db: Session, *, include_summary: bool = True) -> ProjectResponse:
    summary = (
        ProjectSummary(**get_project_summary(db, project.project_id))
        if include_summary
        else None
    )
    return ProjectResponse(
        project_id=project.project_id,
        user_id=project.user_id,
        title=project.title,
        description=project.description,
        source_type=project.source_type,
        cover_image=project.cover_image,
        project_status=project.project_status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        summary=summary,
    )


@router.post("", response_model=ProjectResponse)
def create_script_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = create_project(
        db,
        title=payload.title,
        description=payload.description,
        source_type=payload.source_type,
        user_id=current_user.user_id,
    )
    db.commit()
    db.refresh(project)
    return serialize_project(project, db)


@router.get("", response_model=list[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    return [
        serialize_project(project, db)
        for project in list_projects(db, user_id=current_user.user_id)
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_script_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    return serialize_project(project, db)


@router.patch("/{project_id}", response_model=ProjectResponse)
def patch_script_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    update_project(db, project, payload)
    db.commit()
    db.refresh(project)
    return serialize_project(project, db)


@router.delete("/{project_id}", response_model=ProjectResponse)
def delete_script_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    archive_project(db, project)
    db.commit()
    db.refresh(project)
    return serialize_project(project, db)


@router.post(
    "/{project_id}/candidates/extract",
    response_model=list[CharacterCandidateResponse],
)
def extract_project_candidates(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CharacterCandidateResponse]:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    run_script_intelligence_pipeline(
        db,
        project_id=project_id,
        current_user=current_user if project.user_id else None,
    )
    db.commit()
    return [
        serialize_candidate(candidate)
        for candidate in list_candidates(db, project_id=project_id)
    ]


@router.get(
    "/{project_id}/candidates",
    response_model=list[CharacterCandidateResponse],
)
def get_project_candidates(
    project_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CharacterCandidateResponse]:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    return [
        serialize_candidate(candidate)
        for candidate in list_candidates(
            db,
            project_id=project_id,
            status=status_filter,
        )
    ]


@router.post(
    "/{project_id}/relationships/extract",
    response_model=list[CharacterRelationshipResponse],
)
def extract_project_relationships(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CharacterRelationshipResponse]:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    relationships = extract_relationships_for_project(
        db,
        project_id=project_id,
        user_id=current_user.user_id if project.user_id else None,
    )
    db.commit()
    return [serialize_relationship(relationship) for relationship in relationships]


@router.get(
    "/{project_id}/relationships",
    response_model=list[CharacterRelationshipResponse],
)
def get_project_relationships(
    project_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CharacterRelationshipResponse]:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    return [
        serialize_relationship(relationship)
        for relationship in list_relationships(
            db,
            project_id=project_id,
            status=status_filter,
        )
    ]


@router.get(
    "/{project_id}/relationships/graph",
    response_model=RelationshipGraphResponse,
)
def get_project_relationship_graph(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RelationshipGraphResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)
    graph = build_relationship_graph(
        list_relationships(db, project_id=project_id)
    )
    return RelationshipGraphResponse(**graph)


@router.post(
    "/{project_id}/characters/batch-generate",
    response_model=BatchGenerateResponse,
)
def batch_generate_project_characters(
    project_id: str,
    payload: BatchGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchGenerateResponse:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_user_can_access_project(current_user, project)

    uploaded_files = list(
        db.query(UploadedFile)
        .filter(UploadedFile.project_id == project_id)
        .filter(
            (UploadedFile.user_id == current_user.user_id)
            | UploadedFile.user_id.is_(None)
        )
        .order_by(UploadedFile.created_at.asc(), UploadedFile.id.asc())
    )
    if not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no uploaded files",
        )

    generated = []
    skipped: list[BatchGenerateSkipped] = []
    failed: list[BatchGenerateFailed] = []
    uploaded_file_ids = [uploaded_file.file_id for uploaded_file in uploaded_files]

    for candidate_id in payload.candidate_ids:
        candidate = get_candidate(db, candidate_id)
        if not candidate:
            failed.append(
                BatchGenerateFailed(
                    candidate_id=candidate_id,
                    name="",
                    reason="Candidate not found",
                )
            )
            continue
        if candidate.project_id != project_id:
            failed.append(
                BatchGenerateFailed(
                    candidate_id=candidate.candidate_id,
                    name=candidate.name,
                    reason="Candidate does not belong to this project",
                )
            )
            continue
        try:
            ensure_user_can_access_candidate(current_user, candidate)
        except HTTPException as exc:
            failed.append(
                BatchGenerateFailed(
                    candidate_id=candidate.candidate_id,
                    name=candidate.name,
                    reason=str(exc.detail),
                )
            )
            continue
        can_generate, skip_reason = can_generate_candidate(candidate)
        if not can_generate:
            skipped.append(
                BatchGenerateSkipped(
                    candidate_id=candidate.candidate_id,
                    name=candidate.name,
                    reason=skip_reason,
                )
            )
            continue

        relationship_hint = (
            payload.relationship_overrides.get(candidate.candidate_id)
            or summarize_relationship_hints(
                get_relationships_for_character(
                    db,
                    project_id=project_id,
                    character_name=candidate_generation_name(candidate),
                )
            )
            or first_relationship_hint(candidate.relationship_hints)
            or payload.default_relationship_hint
        )[:200]
        try:
            character, parsed_documents, profile, _ = generate_character(
                db,
                CharacterGenerateRequest(
                    project_id=project_id,
                    uploaded_file_ids=uploaded_file_ids,
                    target_character_name=candidate_generation_name(candidate),
                    user_persona_name=payload.user_persona_name,
                    relationship_hint=relationship_hint,
                ),
                user_id=current_user.user_id if project.user_id else None,
            )
            mark_candidate_generated(db, candidate)
            db.commit()
            db.refresh(candidate)
            generated.append(
                build_generated_character_response(
                    db,
                    character,
                    parsed_documents,
                    profile,
                )
            )
        except Exception as exc:
            db.rollback()
            failed.append(
                BatchGenerateFailed(
                    candidate_id=candidate.candidate_id,
                    name=candidate.name,
                    reason=f"{exc.__class__.__name__}: {exc}",
                )
            )

    return BatchGenerateResponse(generated=generated, skipped=skipped, failed=failed)


def first_relationship_hint(raw_value: str) -> str:
    hints = parse_json_list(raw_value)
    return hints[0] if hints else ""
