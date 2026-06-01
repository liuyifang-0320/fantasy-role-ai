from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Memory, User
from app.schemas.memory import (
    MemoryDebugResponse,
    MemoryDeleteResponse,
    MemoryItem,
    MemoryPatchRequest,
    MemoryResponse,
    MemoryUpdateRequest,
    MemoryUpdateResponse,
)
from app.services.access_control import (
    ensure_user_can_access_character,
    ensure_user_can_access_memory,
)
from app.services.auth import get_current_user
from app.services.characters import get_character
from app.services.memories import (
    MEMORY_RESPONSE_KEYS,
    MEMORY_TYPES,
    create_memory,
    deactivate_memory,
    get_memory,
    group_memories,
    list_active_memories,
    list_all_memories,
    update_memory,
)


router = APIRouter()


def serialize_memory(memory: Memory) -> MemoryItem:
    return MemoryItem(
        memory_id=memory.memory_id,
        user_id=memory.user_id,
        project_id=memory.project_id,
        memory_content=memory.content,
        memory_type=memory.memory_type,
        importance=memory.importance,
        source=memory.source,
        is_active=memory.is_active,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


def ensure_character(db: Session, character_id: str, current_user: User):
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    ensure_user_can_access_character(current_user, character)
    return character


def ensure_memory_type(memory_type: str) -> None:
    if memory_type not in MEMORY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported memory_type",
        )


@router.get("/{character_id}/debug", response_model=MemoryDebugResponse)
def get_memory_debug(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryDebugResponse:
    character = ensure_character(db, character_id, current_user)
    return MemoryDebugResponse(
        character_id=character_id,
        user_id=character.user_id,
        project_id=character.project_id,
        memories=[serialize_memory(memory) for memory in list_all_memories(db, character_id)],
    )


@router.get("/{character_id}", response_model=MemoryResponse)
def get_memory_list(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryResponse:
    character = ensure_character(db, character_id, current_user)
    grouped = group_memories(list_active_memories(db, character_id))
    payload = {
        response_key: [serialize_memory(memory) for memory in grouped[memory_type]]
        for memory_type, response_key in MEMORY_RESPONSE_KEYS.items()
    }
    return MemoryResponse(
        character_id=character_id,
        user_id=character.user_id,
        project_id=character.project_id,
        **payload,
    )


@router.post("/update", response_model=MemoryUpdateResponse)
def create_or_update_memory(
    payload: MemoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryUpdateResponse:
    character = ensure_character(db, payload.character_id, current_user)
    ensure_memory_type(payload.memory_type)

    memory = create_memory(
        db,
        character_id=payload.character_id,
        project_id=character.project_id,
        user_id=character.user_id,
        memory_type=payload.memory_type,
        content=payload.memory_content,
        importance=payload.importance,
        source="user_manual",
    )
    db.commit()
    db.refresh(memory)
    return MemoryUpdateResponse(
        success=True,
        memory_id=memory.memory_id,
        message="Memory saved successfully",
        memory=serialize_memory(memory),
    )


@router.patch("/{memory_id}", response_model=MemoryUpdateResponse)
def patch_memory(
    memory_id: str,
    payload: MemoryPatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryUpdateResponse:
    memory = get_memory(db, memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )
    ensure_user_can_access_memory(current_user, memory)
    if payload.memory_type is not None:
        ensure_memory_type(payload.memory_type)

    memory = update_memory(
        db,
        memory,
        content=payload.resolved_content(),
        memory_type=payload.memory_type,
        importance=payload.importance,
    )
    db.commit()
    db.refresh(memory)
    return MemoryUpdateResponse(
        success=True,
        memory_id=memory.memory_id,
        message="Memory updated successfully",
        memory=serialize_memory(memory),
    )


@router.delete("/{memory_id}", response_model=MemoryDeleteResponse)
def delete_memory(
    memory_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryDeleteResponse:
    memory = get_memory(db, memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )
    ensure_user_can_access_memory(current_user, memory)
    deactivate_memory(db, memory)
    db.commit()
    return MemoryDeleteResponse(
        success=True,
        memory_id=memory_id,
        message="Memory removed successfully",
    )
