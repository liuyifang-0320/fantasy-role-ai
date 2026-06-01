from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession
from app.services.character_relationships import get_relationships_for_character
from app.services.character_settings import get_or_create_settings
from app.services.content_safety import (
    check_assistant_reply,
    check_user_message,
    create_safety_log,
)
from app.services.ids import next_prefixed_id
from app.services.knowledge_retriever import retrieve_knowledge
from app.services.llm_provider import MockLLMProvider, get_llm_provider
from app.services.memories import create_memory, dedupe_memory, list_active_memories
from app.services.memory_extractor import extract_memory_candidates
from app.services.prompt_builder import build_prompt_bundle


PROMPT_SNAPSHOT_LIMIT = 2000


def get_or_create_session(
    db: Session,
    character_id: str,
    project_id: str | None,
    user_id: str | None,
    requested_session_id: str | None,
    first_message: str,
) -> ChatSession:
    if requested_session_id:
        session = db.scalar(
            select(ChatSession).where(ChatSession.session_id == requested_session_id)
        )
        if session:
            if session.character_id != character_id:
                raise ValueError("Session does not belong to this character")
            if session.project_id and project_id and session.project_id != project_id:
                raise ValueError("Session does not belong to this project")
            if not session.project_id and project_id:
                session.project_id = project_id
            if session.user_id and user_id and session.user_id != user_id:
                raise ValueError("Session does not belong to current user")
            if not session.user_id and user_id:
                session.user_id = user_id
            return session

    session = ChatSession(
        session_id=requested_session_id or next_prefixed_id(db, ChatSession, "session"),
        user_id=user_id,
        project_id=project_id,
        character_id=character_id,
        title=build_session_title(first_message),
    )
    db.add(session)
    db.flush()
    return session


def build_session_title(first_message: str) -> str:
    stripped = " ".join(first_message.split())
    return stripped[:24] or "新的对话"


def create_message(
    db: Session,
    *,
    session_id: str,
    character_id: str,
    project_id: str | None,
    user_id: str | None,
    role: str,
    content: str,
    pet_action: str | None = None,
    memory_hint: str | None = None,
    prompt_snapshot: str = "",
) -> ChatMessage:
    message = ChatMessage(
        message_id=next_prefixed_id(db, ChatMessage, "msg"),
        user_id=user_id,
        project_id=project_id,
        session_id=session_id,
        character_id=character_id,
        role=role,
        content=content,
        pet_action=pet_action,
        memory_hint=memory_hint,
        prompt_snapshot=prompt_snapshot[:PROMPT_SNAPSHOT_LIMIT],
    )
    db.add(message)
    db.flush()
    return message


def list_session_messages(db: Session, session_id: str) -> list[ChatMessage]:
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        )
    )


def list_character_sessions(db: Session, character_id: str) -> list[ChatSession]:
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.character_id == character_id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        )
    )


def get_recent_messages(
    db: Session,
    session_id: str,
    *,
    limit: int = 6,
) -> list[ChatMessage]:
    messages = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
    )
    return list(reversed(messages))


def run_chat_turn(
    db: Session,
    *,
    character,
    profile,
    requested_session_id: str | None,
    user_message: str,
) -> tuple[
    ChatSession,
    ChatMessage,
    ChatMessage,
    dict,
    dict,
    dict,
    dict,
]:
    session = get_or_create_session(
        db,
        character_id=character.character_id,
        project_id=character.project_id,
        user_id=character.user_id,
        requested_session_id=requested_session_id,
        first_message=user_message,
    )
    recent_messages = get_recent_messages(db, session.session_id)
    user_safety = check_user_message(
        user_message,
        build_safety_context(character, session.session_id),
    )
    user_record = create_message(
        db,
        session_id=session.session_id,
        character_id=character.character_id,
        project_id=character.project_id,
        user_id=character.user_id,
        role="user",
        content=user_message,
    )
    log_safety_result(
        db,
        result=user_safety,
        direction="user_input",
        input_text=user_message,
        character=character,
        session_id=session.session_id,
        message_id=user_record.message_id,
    )

    if user_safety.action == "block":
        return build_blocked_chat_turn(
            db,
            character=character,
            profile=profile,
            session=session,
            user_record=user_record,
            recent_messages=recent_messages,
            user_message=user_message,
            user_safety=user_safety,
        )

    character_settings = get_or_create_settings(db, character)
    retrieval_result = retrieve_knowledge(
        db,
        character=character,
        profile=profile,
        query=user_message,
        spoiler_mode=character_settings.spoiler_mode,
    )
    active_memories = list_active_memories(db, character.character_id, limit=12)
    character_relationships = get_relationships_for_character(
        db,
        project_id=character.project_id,
        character_name=character.character_name,
    )
    prompt_bundle = build_prompt_bundle(
        character=character,
        profile=profile,
        recent_messages=recent_messages,
        user_message=user_message,
        retrieved_chunks=retrieval_result.chunks,
        retrieval_scope=retrieval_result.retrieval_scope,
        retrieval_project_scope=retrieval_result.retrieval_project_scope,
        project_id=retrieval_result.project_id or character.project_id,
        active_memories=active_memories,
        character_relationships=character_relationships,
        character_settings=character_settings,
        safety_warnings=(
            user_safety.matched_categories if user_safety.action == "warn" else []
        ),
    )

    provider = get_llm_provider()
    try:
        provider_result = provider.generate_reply(prompt_bundle)
    except Exception as exc:
        provider_result = MockLLMProvider(
            configured_provider=provider.configured_provider,
            fallback=True,
            fallback_reason=build_provider_failure_reason(
                provider.provider_name,
                exc,
            ),
        ).generate_reply(prompt_bundle)

    assistant_safety = check_assistant_reply(
        str(provider_result["reply"]),
        build_safety_context(character, session.session_id),
    )
    if assistant_safety.action == "replace":
        provider_result["reply"] = assistant_safety.safe_reply
        provider_result["pet_action"] = safety_pet_action(
            assistant_safety.matched_categories
        )
        provider_result["memory_hint"] = "本轮回复已被内容安全兜底替换。"

    memory_debug = save_memory_candidates(
        db,
        character=character,
        user_message=user_message,
        assistant_reply=str(provider_result["reply"]),
        pet_action=str(provider_result["pet_action"]),
        session_id=session.session_id,
    )
    memory_hint = build_memory_hint(
        str(provider_result["memory_hint"]),
        int(memory_debug["created_count"]),
    )
    assistant_message = create_message(
        db,
        session_id=session.session_id,
        character_id=character.character_id,
        project_id=character.project_id,
        user_id=character.user_id,
        role="assistant",
        content=str(provider_result["reply"]),
        pet_action=str(provider_result["pet_action"]),
        memory_hint=memory_hint,
        prompt_snapshot=build_prompt_snapshot(prompt_bundle),
    )
    log_safety_result(
        db,
        result=assistant_safety,
        direction="assistant_output",
        input_text=str(provider_result["reply"]),
        character=character,
        session_id=session.session_id,
        message_id=assistant_message.message_id,
    )
    session.updated_at = assistant_message.created_at
    return (
        session,
        user_record,
        assistant_message,
        prompt_bundle,
        provider_result,
        memory_debug,
        build_safety_debug(user_safety, assistant_safety),
    )


def build_blocked_chat_turn(
    db: Session,
    *,
    character,
    profile,
    session: ChatSession,
    user_record: ChatMessage,
    recent_messages: list[ChatMessage],
    user_message: str,
    user_safety,
):
    character_settings = get_or_create_settings(db, character)
    prompt_bundle = build_prompt_bundle(
        character=character,
        profile=profile,
        recent_messages=recent_messages,
        user_message=user_message,
        retrieved_chunks=[],
        retrieval_scope="none",
        retrieval_project_scope="none",
        project_id=character.project_id,
        active_memories=[],
        character_relationships=[],
        character_settings=character_settings,
        safety_warnings=user_safety.matched_categories,
    )
    provider_result = {
        "reply": user_safety.safe_reply,
        "pet_action": safety_pet_action(user_safety.matched_categories),
        "memory_hint": "本轮触发内容安全保护，未进入普通模型回复。",
        "provider": "mock",
        "model": "safety-rule",
        "fallback": False,
        "fallback_reason": None,
    }
    assistant_message = create_message(
        db,
        session_id=session.session_id,
        character_id=character.character_id,
        project_id=character.project_id,
        user_id=character.user_id,
        role="assistant",
        content=str(provider_result["reply"]),
        pet_action=str(provider_result["pet_action"]),
        memory_hint=str(provider_result["memory_hint"]),
        prompt_snapshot=str(prompt_bundle["safety_prompt"])[:PROMPT_SNAPSHOT_LIMIT],
    )
    session.updated_at = assistant_message.created_at
    return (
        session,
        user_record,
        assistant_message,
        prompt_bundle,
        provider_result,
        {"created_count": 0, "candidates": []},
        build_safety_debug(user_safety, None),
    )


def build_provider_failure_reason(provider_name: str, exc: Exception) -> str:
    return f"{provider_name} call failed: {exc.__class__.__name__}"


def save_memory_candidates(
    db: Session,
    *,
    character,
    user_message: str,
    assistant_reply: str,
    pet_action: str,
    session_id: str,
) -> dict[str, int | list[dict[str, str | int | bool]]]:
    candidates = extract_memory_candidates(
        character=character,
        user_message=user_message,
        assistant_reply=assistant_reply,
        pet_action=pet_action,
        session_id=session_id,
    )
    created_count = 0
    debug_candidates: list[dict[str, str | int | bool]] = []
    for candidate in candidates:
        content = str(candidate["content"])
        saved = False
        reason = str(candidate["reason"])
        if int(candidate["importance"]) >= 3:
            existing = dedupe_memory(db, character.character_id, content)
            if existing:
                reason = f"{reason}；已存在相同 active memory，未重复保存"
            else:
                create_memory(
                    db,
                    character_id=character.character_id,
                    project_id=character.project_id,
                    user_id=character.user_id,
                    memory_type=str(candidate["memory_type"]),
                    content=content,
                    importance=int(candidate["importance"]),
                    source="chat_auto",
                )
                saved = True
                created_count += 1
        debug_candidates.append(
            {
                "memory_type": str(candidate["memory_type"]),
                "content": content,
                "importance": int(candidate["importance"]),
                "saved": saved,
                "reason": reason,
            }
        )
    return {"created_count": created_count, "candidates": debug_candidates}


def build_memory_hint(provider_memory_hint: str, created_count: int) -> str:
    if created_count > 0:
        return "角色记住了这件事。"
    return provider_memory_hint


def build_prompt_snapshot(prompt_bundle: dict) -> str:
    return "\n\n".join(
        [
            str(prompt_bundle["system_prompt"]),
            str(prompt_bundle["settings_prompt"]),
            str(prompt_bundle["safety_prompt"]),
            str(prompt_bundle["memory_prompt"]),
            str(prompt_bundle["relationship_prompt"]),
            str(prompt_bundle["knowledge_prompt"]),
            str(prompt_bundle["context_prompt"]),
            str(prompt_bundle["user_prompt"]),
        ]
    )


def build_safety_context(character, session_id: str | None = None) -> dict:
    return {
        "character": character,
        "user_id": character.user_id,
        "project_id": character.project_id,
        "session_id": session_id,
    }


def log_safety_result(
    db: Session,
    *,
    result,
    direction: str,
    input_text: str,
    character,
    session_id: str | None,
    message_id: str | None,
) -> None:
    if not result.matched_categories:
        return
    create_safety_log(
        db,
        result=result,
        direction=direction,
        input_text=input_text,
        user_id=character.user_id,
        project_id=character.project_id,
        character_id=character.character_id,
        session_id=session_id,
        message_id=message_id,
    )


def safety_pet_action(categories: list[str]) -> str:
    if "self_harm" in categories or "dependency_risk" in categories:
        return "comfort"
    return "thinking"


def build_safety_debug(user_safety, assistant_safety) -> dict[str, str | list[str]]:
    categories = list(user_safety.matched_categories)
    assistant_action = "allow"
    if assistant_safety:
        assistant_action = assistant_safety.action
        for category in assistant_safety.matched_categories:
            if category not in categories:
                categories.append(category)
    return {
        "user_input_action": user_safety.action,
        "assistant_output_action": assistant_action,
        "matched_categories": categories,
    }
