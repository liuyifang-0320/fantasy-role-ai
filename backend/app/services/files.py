from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import UploadedFile
from app.services.ids import next_prefixed_id
from app.services.access_control import ensure_user_can_access_project
from app.services.projects import get_project
from app.services.storage_provider import get_storage_provider


def get_uploaded_file(db: Session, file_id: str) -> UploadedFile | None:
    return db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()


def save_uploaded_file(
    db: Session,
    file: UploadFile,
    *,
    project_id: str | None = None,
    user=None,
) -> UploadedFile:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in settings.allowed_upload_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )
    normalized_project_id = project_id.strip() if project_id else None
    if normalized_project_id:
        project = get_project(db, normalized_project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        if user is not None:
            ensure_user_can_access_project(user, project)

    file_id = next_prefixed_id(db, UploadedFile, "file")
    safe_filename = Path(file.filename or "upload").name
    saved_filename = f"{file_id}_{safe_filename}"
    content_type = file.content_type or "application/octet-stream"
    storage_result = get_storage_provider().save_upload(
        file,
        saved_filename,
        content_type,
    )

    uploaded_file = UploadedFile(
        file_id=file_id,
        user_id=user.user_id if user is not None else None,
        project_id=normalized_project_id,
        filename=safe_filename,
        file_type=extension.removeprefix("."),
        file_path=storage_result.file_path,
        storage_provider=storage_result.storage_provider,
        storage_key=storage_result.storage_key,
        public_url=storage_result.public_url,
        content_type=storage_result.content_type,
        file_size=storage_result.file_size,
        upload_status="uploaded",
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    return uploaded_file
