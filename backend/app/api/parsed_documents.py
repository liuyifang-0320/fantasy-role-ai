from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ParsedDocument, User
from app.schemas.file import ParsedDocumentDetail
from app.services.access_control import ensure_user_can_access_parsed_document
from app.services.auth import get_current_user
from app.services.profile_extractor import parse_json_list


router = APIRouter()


@router.get("/{parsed_id}", response_model=ParsedDocumentDetail)
def get_parsed_document(
    parsed_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ParsedDocumentDetail:
    parsed_document = db.scalar(
        select(ParsedDocument).where(ParsedDocument.parsed_id == parsed_id)
    )
    if not parsed_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parsed document not found",
        )
    ensure_user_can_access_parsed_document(current_user, parsed_document)

    return ParsedDocumentDetail(
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
        raw_text=parsed_document.raw_text,
    )
