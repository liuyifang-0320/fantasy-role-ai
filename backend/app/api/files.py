from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.file import (
    FileUploadResponse,
    ParsedDocumentSummary,
)
from app.services.files import get_uploaded_file, save_uploaded_file
from app.services.parser import get_latest_parsed_document, parse_uploaded_file
from app.services.profile_extractor import parse_json_list
from app.services.access_control import (
    ensure_user_can_access_file,
    ensure_user_can_access_parsed_document,
)
from app.services.auth import get_current_user


router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
def upload_file(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileUploadResponse:
    uploaded_file = save_uploaded_file(
        db,
        file,
        project_id=project_id,
        user=current_user,
    )
    return FileUploadResponse(
        file_id=uploaded_file.file_id,
        user_id=uploaded_file.user_id,
        project_id=uploaded_file.project_id,
        filename=uploaded_file.filename,
        file_type=uploaded_file.file_type,
        file_path=uploaded_file.file_path,
        storage_provider=uploaded_file.storage_provider,
        storage_key=uploaded_file.storage_key,
        public_url=uploaded_file.public_url,
        content_type=uploaded_file.content_type,
        file_size=uploaded_file.file_size,
        upload_status=uploaded_file.upload_status,
    )


def serialize_parsed_document(parsed_document) -> ParsedDocumentSummary:
    return ParsedDocumentSummary(
        parsed_id=parsed_document.parsed_id,
        file_id=parsed_document.file_id,
        user_id=parsed_document.user_id,
        project_id=parsed_document.project_id,
        filename=parsed_document.filename,
        file_type=parsed_document.file_type,
        parse_status=parsed_document.parse_status,
        text_preview=parsed_document.text_preview,
        word_count=parsed_document.word_count,
        ocr_provider=parsed_document.ocr_provider or "",
        ocr_confidence=parsed_document.ocr_confidence or 0.0,
        ocr_error=parsed_document.ocr_error,
        safety_warning=parsed_document.safety_warning or "",
        safety_categories=parse_json_list(parsed_document.safety_categories or "[]"),
    )


@router.post("/{file_id}/parse", response_model=ParsedDocumentSummary)
def parse_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ParsedDocumentSummary:
    uploaded_file = get_uploaded_file(db, file_id)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    ensure_user_can_access_file(current_user, uploaded_file)
    parsed_document = parse_uploaded_file(db, uploaded_file)
    return serialize_parsed_document(parsed_document)


@router.get("/{file_id}/parsed", response_model=ParsedDocumentSummary)
def get_parsed_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ParsedDocumentSummary:
    uploaded_file = get_uploaded_file(db, file_id)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    ensure_user_can_access_file(current_user, uploaded_file)
    parsed_document = get_latest_parsed_document(db, file_id)
    if not parsed_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parsed document not found",
        )
    ensure_user_can_access_parsed_document(current_user, parsed_document)
    return serialize_parsed_document(parsed_document)
