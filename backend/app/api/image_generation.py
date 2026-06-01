from fastapi import APIRouter

from app.schemas.pet_asset import ImageGenerationStatusResponse
from app.services.image_generation_provider import get_image_generation_status


router = APIRouter()


@router.get("/status", response_model=ImageGenerationStatusResponse)
def get_status() -> ImageGenerationStatusResponse:
    return ImageGenerationStatusResponse(**get_image_generation_status())
