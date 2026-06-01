from fastapi import APIRouter

from app.core.config import settings
from app.schemas.safety import SafetyStatusResponse


router = APIRouter()


@router.get("/status", response_model=SafetyStatusResponse)
def get_safety_status() -> SafetyStatusResponse:
    return SafetyStatusResponse(
        safety_mode=settings.safety_mode,
        strict_level=settings.safety_strict_level,
        debug_output_enabled=settings.enable_debug_output,
        user_data_export_enabled=settings.enable_user_data_export,
        user_data_delete_enabled=settings.enable_user_data_delete,
        privacy_contact_email=settings.privacy_contact_email,
    )
