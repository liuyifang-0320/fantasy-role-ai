import json

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import ScriptChunk, ScriptSegment
from app.services.ids import next_prefixed_id


MAX_SCRIPT_CHUNK_SIZE = 760


def build_script_chunks(
    db: Session,
    segments: list[ScriptSegment],
    *,
    character_scope: str = "",
) -> list[ScriptChunk]:
    if not segments:
        return []
    parsed_ids = {segment.parsed_document_id for segment in segments}
    for parsed_id in parsed_ids:
        db.execute(delete(ScriptChunk).where(ScriptChunk.parsed_document_id == parsed_id))

    saved: list[ScriptChunk] = []
    for segment in segments:
        chunks = split_segment_text(segment.clean_content)
        for index, chunk_text in enumerate(chunks, start=1):
            metadata = {
                "filename": segment.source_filename,
                "segment_type": segment.segment_type,
                "visibility": segment.visibility,
                "spoiler_level": segment.spoiler_level,
                "possible_characters": [character_scope] if character_scope else [],
                "is_dialogue": segment.segment_type == "dialogue",
                "is_truth": segment.segment_type in {"truth_reveal", "final_mission", "hidden_secret"},
                "is_instruction": segment.segment_type == "player_instruction",
            }
            chunk = ScriptChunk(
                chunk_id=next_prefixed_id(db, ScriptChunk, "chunk"),
                user_id=segment.user_id,
                project_id=segment.project_id,
                parsed_document_id=segment.parsed_document_id,
                segment_id=segment.segment_id,
                chunk_text=chunk_text,
                clean_text=chunk_text,
                chunk_index=index,
                metadata_json=json.dumps(metadata, ensure_ascii=False),
                document_type=segment.segment_type,
                owner_character_name=character_scope,
                perspective="self" if character_scope else "unknown",
                visibility=segment.visibility,
                spoiler_level=segment.spoiler_level,
                source_type="parsed_text",
                character_scope=character_scope,
            )
            db.add(chunk)
            db.flush()
            saved.append(chunk)
    return saved


def split_segment_text(text: str) -> list[str]:
    clean = (text or "").strip()
    if not clean:
        return []
    if len(clean) <= MAX_SCRIPT_CHUNK_SIZE:
        return [clean]
    chunks: list[str] = []
    current = ""
    for line in clean.splitlines():
        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) <= MAX_SCRIPT_CHUNK_SIZE:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = line
    if current:
        chunks.append(current)
    return chunks
