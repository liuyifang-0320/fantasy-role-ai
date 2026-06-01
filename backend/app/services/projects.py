from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Character, KnowledgeChunk, ParsedDocument, ScriptProject, UploadedFile
from app.services.ids import next_prefixed_id


SOURCE_TYPES = {"upload", "manual", "demo"}
PROJECT_STATUSES = {"active", "archived"}


def normalize_source_type(source_type: str | None) -> str:
    value = (source_type or "upload").strip() or "upload"
    return value if value in SOURCE_TYPES else "upload"


def normalize_project_status(project_status: str | None) -> str:
    value = (project_status or "active").strip() or "active"
    return value if value in PROJECT_STATUSES else "active"


def create_project(
    db: Session,
    *,
    title: str,
    description: str = "",
    source_type: str = "upload",
    user_id: str | None = None,
) -> ScriptProject:
    project = ScriptProject(
        project_id=next_prefixed_id(db, ScriptProject, "project"),
        user_id=user_id,
        title=title.strip(),
        description=description.strip(),
        source_type=normalize_source_type(source_type),
        project_status="active",
    )
    db.add(project)
    db.flush()
    return project


def list_projects(db: Session, user_id: str | None = None) -> list[ScriptProject]:
    statement = select(ScriptProject)
    if user_id:
        statement = statement.where(
            or_(ScriptProject.user_id == user_id, ScriptProject.user_id.is_(None))
        )
    return list(
        db.scalars(
            statement.order_by(
                ScriptProject.updated_at.desc(),
                ScriptProject.created_at.desc(),
                ScriptProject.id.desc(),
            )
        )
    )


def get_project(db: Session, project_id: str) -> ScriptProject | None:
    return db.scalar(
        select(ScriptProject).where(ScriptProject.project_id == project_id)
    )


def update_project(db: Session, project: ScriptProject, payload) -> ScriptProject:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if field == "source_type":
            value = normalize_source_type(value)
        if field == "project_status":
            value = normalize_project_status(value)
        setattr(project, field, value)
    project.updated_at = datetime.utcnow()
    db.flush()
    return project


def archive_project(db: Session, project: ScriptProject) -> ScriptProject:
    project.project_status = "archived"
    project.updated_at = datetime.utcnow()
    db.flush()
    return project


def get_project_summary(db: Session, project_id: str) -> dict[str, int | datetime | None]:
    files = list(
        db.scalars(select(UploadedFile).where(UploadedFile.project_id == project_id))
    )
    parsed_documents = list(
        db.scalars(
            select(ParsedDocument).where(ParsedDocument.project_id == project_id)
        )
    )
    characters = list(
        db.scalars(select(Character).where(Character.project_id == project_id))
    )
    chunks = list(
        db.scalars(
            select(KnowledgeChunk).where(KnowledgeChunk.project_id == project_id)
        )
    )
    latest_candidates = [
        *(file.created_at for file in files),
        *(parsed.created_at for parsed in parsed_documents),
        *(character.updated_at for character in characters),
        *(chunk.created_at for chunk in chunks),
    ]
    return {
        "file_count": len(files),
        "parsed_document_count": len(parsed_documents),
        "character_count": len(characters),
        "knowledge_chunk_count": len(chunks),
        "latest_updated_at": max(latest_candidates) if latest_candidates else None,
    }
