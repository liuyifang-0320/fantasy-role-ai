from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.characters import serialize_pet_asset
from app.db.session import get_db
from app.models import User
from app.schemas.pet_asset import PetAssetResponse
from app.services.access_control import ensure_user_can_access_pet_asset
from app.services.auth import get_current_user
from app.services.pet_assets import get_pet_asset


router = APIRouter()


@router.get("/{asset_id}", response_model=PetAssetResponse)
def get_pet_asset_detail(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PetAssetResponse:
    asset = get_pet_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet asset not found")
    ensure_user_can_access_pet_asset(current_user, asset)
    return serialize_pet_asset(asset)
