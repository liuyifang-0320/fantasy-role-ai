from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Memory
from app.services.ids import next_prefixed_id


MEMORY_TYPES = {
    "user_preference",
    "relationship",
    "story_interaction",
    "emotional_state",
    "custom",
}
MEMORY_RESPONSE_KEYS = {
    "user_preference": "user_preference_memory",
    "relationship": "relationship_memory",
    "story_interaction": "story_interaction_memory",
    "emotional_state": "emotional_state_memory",
    "custom": "custom_memory",
}
MEMORY_SOURCES = {"chat_auto", "user_manual", "system_mock"}


def normalize_memory_content(content: str) -> str:
    return " ".join(content.strip().split())


def clamp_importance(importance: int | None) -> int:
    if importance is None:
        return 3
    return min(5, max(1, importance))


def list_active_memories(
    db: Session,
    character_id: str,
    *,
    limit: int | None = None,
) -> list[Memory]:
    statement = (
        select(Memory)
        .where(Memory.character_id == character_id, Memory.is_active.is_(True))
        .order_by(
            Memory.importance.desc(),
            Memory.updated_at.desc(),
            Memory.created_at.desc(),
            Memory.id.desc(),
        )
    )
    if limit:
        statement = statement.limit(limit)
    return list(db.scalars(statement))


def list_all_memories(db: Session, character_id: str) -> list[Memory]:
    return list(
        db.scalars(
            select(Memory)
            .where(Memory.character_id == character_id)
            .order_by(Memory.is_active.desc(), Memory.updated_at.desc(), Memory.id.desc())
        )
    )


def get_memory(db: Session, memory_id: str) -> Memory | None:
    return db.scalar(select(Memory).where(Memory.memory_id == memory_id))


def create_memory(
    db: Session,
    *,
    character_id: str,
    project_id: str | None = None,
    user_id: str | None = None,
    memory_type: str,
    content: str,
    importance: int = 3,
    source: str = "user_manual",
) -> Memory:
    memory = Memory(
        memory_id=next_prefixed_id(db, Memory, "mem"),
        user_id=user_id,
        project_id=project_id,
        character_id=character_id,
        memory_type=memory_type,
        content=normalize_memory_content(content),
        importance=clamp_importance(importance),
        source=source if source in MEMORY_SOURCES else "user_manual",
        is_active=True,
    )
    db.add(memory)
    db.flush()
    return memory


def update_memory(
    db: Session,
    memory: Memory,
    *,
    content: str | None = None,
    memory_type: str | None = None,
    importance: int | None = None,
) -> Memory:
    if content is not None:
        memory.content = normalize_memory_content(content)
    if memory_type is not None:
        memory.memory_type = memory_type
    if importance is not None:
        memory.importance = clamp_importance(importance)
    memory.updated_at = datetime.utcnow()
    db.flush()
    return memory


def deactivate_memory(db: Session, memory: Memory) -> Memory:
    memory.is_active = False
    memory.updated_at = datetime.utcnow()
    db.flush()
    return memory


def dedupe_memory(db: Session, character_id: str, content: str) -> Memory | None:
    normalized = normalize_memory_content(content)
    return db.scalar(
        select(Memory).where(
            Memory.character_id == character_id,
            Memory.is_active.is_(True),
            Memory.content == normalized,
        )
    )


def group_memories(memories: list[Memory]) -> dict[str, list[Memory]]:
    grouped = {memory_type: [] for memory_type in MEMORY_TYPES}
    for memory in memories:
        if memory.memory_type in grouped:
            grouped[memory.memory_type].append(memory)
    return grouped
