from fastapi import APIRouter

from app.schemas.ocr import OCRStatusResponse
from app.services.ocr_provider import get_ocr_status


router = APIRouter()


@router.get("/status", response_model=OCRStatusResponse)
def get_status() -> OCRStatusResponse:
    return OCRStatusResponse(**get_ocr_status())
