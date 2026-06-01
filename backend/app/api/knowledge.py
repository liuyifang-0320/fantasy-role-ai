from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ParsedDocument, User
from app.schemas.knowledge import (
    KnowledgeBuildRequest,
    KnowledgeBuildResponse,
    KnowledgeChunkPreview,
    KnowledgeChunkResponse,
    KnowledgeSearchRequest,
    RetrievedKnowledgeChunk,
)
from app.services.characters import get_character
from app.services.access_control import (
    ensure_user_can_access_character,
    ensure_user_can_access_parsed_document,
    ensure_user_can_access_project,
    ensure_user_can_access_resource,
)
from app.services.auth import get_current_user
from app.services.knowledge_chunker import (
    get_chunk,
    list_chunks,
    rebuild_knowledge_chunks,
)
from app.services.knowledge_retriever import retrieve_knowledge
from app.services.profile_extractor import get_latest_profile_for_character
from app.services.projects import get_project


router = APIRouter()


def serialize_chunk(chunk) -> KnowledgeChunkResponse:
    return KnowledgeChunkResponse(
        chunk_id=chunk.chunk_id,
        user_id=chunk.user_id,
        project_id=chunk.project_id,
        parsed_document_id=chunk.parsed_document_id,
        file_id=chunk.file_id,
        character_id=chunk.character_id,
        target_character_name=chunk.target_character_name,
        user_persona_name=chunk.user_persona_name,
        chapter=chunk.chapter,
        chunk_index=chunk.chunk_index,
        content=chunk.content,
        content_preview=chunk.content_preview,
        keywords=chunk.keywords,
        visibility=chunk.visibility,
        source_type=chunk.source_type,
        created_at=chunk.created_at,
    )


def serialize_preview(chunk) -> KnowledgeChunkPreview:
    return KnowledgeChunkPreview(
        chunk_id=chunk.chunk_id,
        chapter=chunk.chapter,
        visibility=chunk.visibility,
        content_preview=chunk.content_preview,
    )


@router.post("/build", response_model=KnowledgeBuildResponse)
def build_knowledge(
    payload: KnowledgeBuildRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBuildResponse:
    parsed_documents = list(
        db.scalars(
            select(ParsedDocument).where(
                ParsedDocument.parsed_id.in_(payload.parsed_document_ids)
            )
        )
    )
    if len(parsed_documents) != len(payload.parsed_document_ids):
        missing_ids = set(payload.parsed_document_ids) - {
            parsed_document.parsed_id for parsed_document in parsed_documents
        }
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown parsed_document_ids: {', '.join(sorted(missing_ids))}",
        )
    for parsed_document in parsed_documents:
        ensure_user_can_access_parsed_document(current_user, parsed_document)
    resolved_project_id = payload.project_id.strip() if payload.project_id else None
    character = get_character(db, payload.character_id) if payload.character_id else None
    if payload.character_id and not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    if character:
        ensure_user_can_access_character(current_user, character)
    if character and character.project_id:
        if resolved_project_id and resolved_project_id != character.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id does not match character project",
            )
        resolved_project_id = character.project_id
    if resolved_project_id:
        project = get_project(db, resolved_project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        ensure_user_can_access_project(current_user, project)
        mismatched_parsed_ids = [
            parsed_document.parsed_id
            for parsed_document in parsed_documents
            if parsed_document.project_id != resolved_project_id
        ]
        if mismatched_parsed_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Parsed documents do not belong to project: "
                    + ", ".join(sorted(mismatched_parsed_ids))
                ),
            )

    chunks = []
    for parsed_document in parsed_documents:
        chunks.extend(
            rebuild_knowledge_chunks(
                db,
                parsed_document,
                target_character_name=payload.target_character_name,
                user_persona_name=payload.user_persona_name,
                character_id=payload.character_id,
                project_id=resolved_project_id,
                user_id=current_user.user_id,
            )
        )
    db.commit()
    return KnowledgeBuildResponse(
        knowledge_chunk_count=len(chunks),
        knowledge_chunks_preview=[serialize_preview(chunk) for chunk in chunks[:5]],
    )


@router.get("/chunks", response_model=list[KnowledgeChunkResponse])
def get_chunks(
    project_id: str | None = Query(default=None),
    character_id: str | None = Query(default=None),
    parsed_document_id: str | None = Query(default=None),
    visibility: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeChunkResponse]:
    if project_id:
        project = get_project(db, project_id)
        if project:
            ensure_user_can_access_project(current_user, project)
    if character_id:
        character = get_character(db, character_id)
        if character:
            ensure_user_can_access_character(current_user, character)
    return [
        serialize_chunk(chunk)
        for chunk in list_chunks(
            db,
            project_id=project_id,
            character_id=character_id,
            parsed_document_id=parsed_document_id,
            visibility=visibility,
            user_id=current_user.user_id,
        )
    ]


@router.get("/chunks/{chunk_id}", response_model=KnowledgeChunkResponse)
def get_chunk_detail(
    chunk_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeChunkResponse:
    chunk = get_chunk(db, chunk_id)
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge chunk not found",
        )
    ensure_user_can_access_resource(current_user, chunk, "Knowledge chunk")
    return serialize_chunk(chunk)


@router.post("/search", response_model=list[RetrievedKnowledgeChunk])
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RetrievedKnowledgeChunk]:
    character = get_character(db, payload.character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    ensure_user_can_access_character(current_user, character)
    requested_project_id = payload.project_id.strip() if payload.project_id else None
    if requested_project_id:
        project = get_project(db, requested_project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        ensure_user_can_access_project(current_user, project)
    if character.project_id and requested_project_id and requested_project_id != character.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id does not match character project",
        )
    profile = get_latest_profile_for_character(db, character.character_id)
    retrieval_result = retrieve_knowledge(
        db,
        character=character,
        profile=profile,
        query=payload.query,
        limit=payload.limit,
        project_id=requested_project_id,
    )
    return [RetrievedKnowledgeChunk(**chunk) for chunk in retrieval_result.chunks]
