from sqlalchemy import func, select
from sqlalchemy.orm import Session


ID_FIELD_BY_PREFIX = {
    "char": "character_id",
    "candidate": "candidate_id",
    "chunk": "chunk_id",
    "file": "file_id",
    "llmrun": "run_id",
    "analysis": "analysis_id",
    "mem": "memory_id",
    "msg": "message_id",
    "parsed": "parsed_id",
    "pet": "pet_id",
    "pet_asset": "asset_id",
    "profile": "profile_id",
    "rel": "relationship_id",
    "session": "session_id",
    "user": "user_id",
}


def next_prefixed_id(db: Session, model, prefix: str) -> str:
    count = db.scalar(select(func.count()).select_from(model)) or 0
    field_name = ID_FIELD_BY_PREFIX.get(prefix, f"{prefix}_id")
    id_column = getattr(model, field_name)
    next_number = count + 1
    while True:
        candidate = f"{prefix}_{next_number:03d}"
        exists = db.scalar(select(id_column).where(id_column == candidate))
        if not exists:
            return candidate
        next_number += 1
