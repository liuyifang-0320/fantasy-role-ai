from fastapi import APIRouter

from app.schemas.system import StorageStatusResponse
from app.services.storage_provider import get_storage_status


router = APIRouter()


@router.get("/status", response_model=StorageStatusResponse)
def get_status() -> StorageStatusResponse:
    return StorageStatusResponse(**get_storage_status())
