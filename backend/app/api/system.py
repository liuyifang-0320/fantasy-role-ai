from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine
from app.schemas.system import SystemHealthResponse
from app.services.image_generation_provider import get_image_generation_status
from app.services.llm_provider import get_llm_status
from app.services.ocr_provider import get_ocr_status
from app.services.storage_provider import get_storage_status


router = APIRouter()


@router.get("/health", response_model=SystemHealthResponse)
def get_system_health() -> SystemHealthResponse:
    database_status = "ok"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "failed"

    storage_status = get_storage_status()
    llm_status = get_llm_status()
    ocr_status = get_ocr_status()
    image_status = get_image_generation_status()
    overall_status = "ok" if database_status == "ok" else "degraded"

    return SystemHealthResponse(
        status=overall_status,
        database=database_status,
        storage=str(storage_status["active_provider"]),
        llm_provider=str(llm_status["active_provider"]),
        ocr_provider=str(ocr_status["active_provider"]),
        image_provider=str(image_status["active_provider"]),
        timestamp=datetime.utcnow().isoformat(),
    )
