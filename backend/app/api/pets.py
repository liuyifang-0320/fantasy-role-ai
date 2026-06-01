from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.schemas.pet import (
    PetActionRequest,
    PetActionResponse,
    PetDetailResponse,
)
from app.services.characters import get_character
from app.services.access_control import ensure_user_can_access_character
from app.services.auth import get_current_user


router = APIRouter()


@router.get("/{character_id}", response_model=PetDetailResponse)
def get_pet(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PetDetailResponse:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)

    return PetDetailResponse(
        character_id=character.character_id,
        pet_name=character.pet.pet_name,
        pet_avatar=character.pet.pet_avatar,
        pet_status=character.pet.pet_status,
        available_actions=character.pet.available_actions,
        intimacy_level=character.intimacy_level,
    )


@router.post("/action", response_model=PetActionResponse)
def update_pet_action(
    payload: PetActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PetActionResponse:
    character = get_character(db, payload.character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)
    if payload.action not in settings.pet_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported action",
        )

    character.pet.pet_status = payload.action
    db.commit()
    return PetActionResponse(
        character_id=character.character_id,
        pet_name=character.pet.pet_name,
        pet_status=character.pet.pet_status,
        action=payload.action,
        message=f"{character.pet.pet_name} is now {payload.action}",
    )
