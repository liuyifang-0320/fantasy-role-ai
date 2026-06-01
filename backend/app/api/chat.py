from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ChatSession, User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    MemoryDebug,
    ProviderDebug,
    PromptDebug,
    SafetyDebug,
)
from app.core.config import settings
from app.services.access_control import (
    ensure_user_can_access_character,
    ensure_user_can_access_resource,
)
from app.services.auth import get_current_user
from app.services.characters import get_character
from app.services.chat_engine import (
    list_character_sessions,
    list_session_messages,
    run_chat_turn,
)
from app.services.profile_extractor import get_latest_profile_for_character


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    character = get_character(db, payload.character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    ensure_user_can_access_character(current_user, character)

    profile = get_latest_profile_for_character(db, character.character_id)
    try:
        (
            session,
            _,
            assistant_message,
            prompt_bundle,
            provider_result,
            memory_debug,
            safety_debug,
        ) = run_chat_turn(
            db,
            character=character,
            profile=profile,
            requested_session_id=payload.session_id,
            user_message=payload.message,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    character.last_message = assistant_message.content
    character.pet.pet_status = assistant_message.pet_action or "idle"
    db.commit()
    return ChatResponse(
        reply=assistant_message.content,
        pet_action=assistant_message.pet_action or "idle",
        memory_hint=assistant_message.memory_hint or "",
        session_id=session.session_id,
        message_id=assistant_message.message_id,
        prompt_debug=(
            PromptDebug(
                project_id=(
                    str(prompt_bundle["project_id"])
                    if prompt_bundle["project_id"]
                    else None
                ),
                retrieval_project_scope=str(prompt_bundle["retrieval_project_scope"]),
                system_prompt_preview=str(prompt_bundle["system_prompt"])[:300],
                context_message_count=int(prompt_bundle["context_message_count"]),
                uses_character_profile=bool(prompt_bundle["uses_character_profile"]),
                uses_character_settings=bool(prompt_bundle["uses_character_settings"]),
                uses_safety_prompt=bool(prompt_bundle["uses_safety_prompt"]),
                settings_prompt_preview=str(prompt_bundle["settings_prompt_preview"]),
                retrieval_scope=str(prompt_bundle["retrieval_scope"]),
                retrieved_chunk_count=int(prompt_bundle["retrieved_chunk_count"]),
                retrieved_chunks_preview=prompt_bundle["retrieved_chunks_debug"],
                active_memory_count=int(prompt_bundle["active_memory_count"]),
                active_memories_preview=prompt_bundle["active_memories_preview"],
                active_relationship_count=int(prompt_bundle["active_relationship_count"]),
                relationships_preview=prompt_bundle["relationships_preview"],
            )
            if settings.enable_prompt_debug and settings.enable_debug_output
            else None
        ),
        memory_debug=(
            MemoryDebug(**memory_debug)
            if settings.enable_debug_output
            else None
        ),
        safety_debug=(
            SafetyDebug(**safety_debug)
            if settings.enable_debug_output
            else None
        ),
        provider_debug=ProviderDebug(
            configured_provider=settings.llm_provider,
            provider=str(provider_result["provider"]),
            model=str(provider_result["model"]),
            base_url_configured=bool(settings.llm_base_url),
            api_key_configured=bool(settings.llm_api_key),
            fallback=bool(provider_result["fallback"]),
            fallback_reason=(
                str(provider_result["fallback_reason"])
                if provider_result["fallback_reason"] and settings.enable_debug_output
                else None
            ),
        ),
    )


@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_chat_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessageResponse]:
    session = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    ensure_user_can_access_resource(current_user, session, "Chat session")
    return [serialize_message(message) for message in list_session_messages(db, session_id)]


@router.get(
    "/chat/characters/{character_id}/sessions",
    response_model=list[ChatSessionResponse],
)
def get_character_chat_sessions(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSessionResponse]:
    character = get_character(db, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    ensure_user_can_access_character(current_user, character)
    return [
        ChatSessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            project_id=session.project_id,
            character_id=session.character_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        for session in list_character_sessions(db, character_id)
    ]


def serialize_message(message) -> ChatMessageResponse:
    return ChatMessageResponse(
        message_id=message.message_id,
        session_id=message.session_id,
        user_id=message.user_id,
        project_id=message.project_id,
        character_id=message.character_id,
        role=message.role,
        content=message.content,
        pet_action=message.pet_action,
        memory_hint=message.memory_hint,
        created_at=message.created_at,
    )
