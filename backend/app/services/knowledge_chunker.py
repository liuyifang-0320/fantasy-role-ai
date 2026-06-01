import re
from collections import Counter

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import KnowledgeChunk, ParsedDocument, ScriptChunk
from app.services.ids import next_prefixed_id


TARGET_CHUNK_SIZE = 650
MIN_CHUNK_SIZE = 500
MAX_CHUNK_SIZE = 800
PREVIEW_LIMIT = 120
DOMAIN_KEYWORDS = (
    "情侣",
    "恋人",
    "喜欢",
    "爱",
    "分别",
    "重逢",
    "秘密",
    "凶手",
    "神社",
    "旧街区",
    "线索",
    "证据",
)
HIDDEN_MARKERS = ("凶手", "真相", "杀人", "伪装", "秘密", "不能说", "隐瞒")
CHAPTER_PATTERN = re.compile(
    r"^(第一幕|第二幕|第[0-9一二三四五六七八九十]+章|Chapter\s+[0-9]+)",
    re.IGNORECASE,
)
STOPWORDS = {
    "一个",
    "我们",
    "他们",
    "自己",
    "这个",
    "那个",
    "现在",
    "已经",
    "还是",
    "因为",
    "所以",
    "如果",
    "但是",
    "没有",
    "不是",
    "可以",
}


def rebuild_knowledge_chunks(
    db: Session,
    parsed_document: ParsedDocument,
    *,
    target_character_name: str,
    user_persona_name: str,
    character_id: str | None = None,
    project_id: str | None = None,
    user_id: str | None = None,
) -> list[KnowledgeChunk]:
    resolved_project_id = project_id if project_id is not None else parsed_document.project_id
    resolved_user_id = user_id if user_id is not None else parsed_document.user_id
    delete_statement = delete(KnowledgeChunk).where(
        KnowledgeChunk.parsed_document_id == parsed_document.parsed_id
    )
    if character_id:
        delete_statement = delete_statement.where(
            KnowledgeChunk.character_id == character_id
        )
    else:
        delete_statement = delete_statement.where(KnowledgeChunk.character_id.is_(None))
    db.execute(delete_statement)

    script_chunks = list(
        db.scalars(
            select(ScriptChunk)
            .where(ScriptChunk.parsed_document_id == parsed_document.parsed_id)
            .order_by(ScriptChunk.chunk_index.asc(), ScriptChunk.id.asc())
        )
    )
    chunks = [
        {
            "content": script_chunk.clean_text or script_chunk.chunk_text,
            "visibility": script_chunk.visibility,
            "spoiler_level": script_chunk.spoiler_level,
            "segment_type": read_script_chunk_segment_type(script_chunk),
            "character_scope": script_chunk.character_scope or target_character_name.strip(),
            "metadata_json": script_chunk.metadata_json or "{}",
        }
        for script_chunk in script_chunks
        if (script_chunk.clean_text or script_chunk.chunk_text).strip()
    ] or [
        {
            "content": chunk,
            "visibility": determine_visibility(chunk, target_character_name),
            "spoiler_level": "heavy" if contains_hidden_marker(chunk) else "none",
            "segment_type": "unknown",
            "character_scope": target_character_name.strip(),
            "metadata_json": "{}",
        }
        for chunk in split_into_chunks(parsed_document.raw_text)
    ]
    saved_chunks: list[KnowledgeChunk] = []
    current_chapter = "未分章"
    source_type = "mock_ocr" if parsed_document.parse_status == "mock_ocr" else "parsed_text"

    for index, chunk_data in enumerate(chunks, start=1):
        raw_chunk = str(chunk_data["content"])
        chapter = detect_chapter(raw_chunk)
        if chapter:
            current_chapter = chapter
        knowledge_chunk = KnowledgeChunk(
            chunk_id=next_prefixed_id(db, KnowledgeChunk, "chunk"),
            user_id=resolved_user_id,
            project_id=resolved_project_id,
            parsed_document_id=parsed_document.parsed_id,
            file_id=parsed_document.file_id,
            character_id=character_id,
            target_character_name=target_character_name.strip(),
            user_persona_name=user_persona_name.strip(),
            chapter=current_chapter,
            chunk_index=index,
            content=raw_chunk,
            content_preview=build_preview(raw_chunk),
            keywords=",".join(
                extract_keywords(
                    raw_chunk,
                    target_character_name=target_character_name,
                    user_persona_name=user_persona_name,
                )
            ),
            visibility=str(chunk_data["visibility"]),
            segment_type=str(chunk_data["segment_type"]),
            spoiler_level=str(chunk_data["spoiler_level"]),
            character_scope=str(chunk_data["character_scope"]),
            metadata_json=str(chunk_data["metadata_json"]),
            source_type=source_type,
        )
        db.add(knowledge_chunk)
        db.flush()
        saved_chunks.append(knowledge_chunk)

    return saved_chunks


def read_script_chunk_segment_type(script_chunk: ScriptChunk) -> str:
    if not script_chunk.metadata_json:
        return "unknown"
    try:
        import json

        metadata = json.loads(script_chunk.metadata_json)
    except Exception:
        return "unknown"
    return str(metadata.get("segment_type") or "unknown")


def split_into_chunks(raw_text: str) -> list[str]:
    normalized = raw_text.lstrip("\ufeff").strip()
    if not normalized:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", normalized)
        if paragraph.strip()
    ]
    expanded_paragraphs: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= MAX_CHUNK_SIZE:
            expanded_paragraphs.append(paragraph)
        else:
            expanded_paragraphs.extend(split_long_paragraph(paragraph))

    chunks: list[str] = []
    current = ""
    for paragraph in expanded_paragraphs:
        if current and contains_hidden_marker(current) != contains_hidden_marker(paragraph):
            chunks.append(current)
            current = paragraph
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= MAX_CHUNK_SIZE:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


def split_long_paragraph(paragraph: str) -> list[str]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[。！？!?])", paragraph)
        if sentence.strip()
    ]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current}{sentence}" if current else sentence
        if len(candidate) <= MAX_CHUNK_SIZE:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = sentence
    if current:
        chunks.append(current)
    return chunks


def detect_chapter(content: str) -> str | None:
    for line in content.splitlines():
        match = CHAPTER_PATTERN.match(line.lstrip("\ufeff").strip())
        if match:
            return match.group(1)
    return None


def extract_keywords(
    content: str,
    *,
    target_character_name: str,
    user_persona_name: str,
) -> list[str]:
    keywords: list[str] = []
    for candidate in (target_character_name.strip(), user_persona_name.strip(), *DOMAIN_KEYWORDS):
        if candidate and candidate in content and candidate not in keywords:
            keywords.append(candidate)

    chinese_tokens = re.findall(r"[\u4e00-\u9fff]{2,4}", content)
    token_counts = Counter(
        token
        for token in chinese_tokens
        if token not in STOPWORDS and token not in keywords
    )
    keywords.extend(token for token, _ in token_counts.most_common(5))
    return keywords


def determine_visibility(content: str, target_character_name: str) -> str:
    if contains_hidden_marker(content):
        return "hidden"
    if target_character_name and target_character_name in content:
        return "self_only"
    return "public"


def build_preview(content: str, limit: int = PREVIEW_LIMIT) -> str:
    return " ".join(content.split())[:limit]


def contains_hidden_marker(content: str) -> bool:
    return any(marker in content for marker in HIDDEN_MARKERS)


def list_chunks(
    db: Session,
    *,
    project_id: str | None = None,
    character_id: str | None = None,
    parsed_document_id: str | None = None,
    visibility: str | None = None,
    user_id: str | None = None,
) -> list[KnowledgeChunk]:
    statement = select(KnowledgeChunk)
    if user_id:
        statement = statement.where(
            (KnowledgeChunk.user_id == user_id) | KnowledgeChunk.user_id.is_(None)
        )
    if project_id:
        statement = statement.where(KnowledgeChunk.project_id == project_id)
    if character_id:
        statement = statement.where(KnowledgeChunk.character_id == character_id)
    if parsed_document_id:
        statement = statement.where(
            KnowledgeChunk.parsed_document_id == parsed_document_id
        )
    if visibility:
        statement = statement.where(KnowledgeChunk.visibility == visibility)
    return list(
        db.scalars(statement.order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.id.desc()))
    )


def get_chunk(db: Session, chunk_id: str) -> KnowledgeChunk | None:
    return db.scalar(
        select(KnowledgeChunk).where(KnowledgeChunk.chunk_id == chunk_id)
    )


def list_character_chunk_previews(
    db: Session,
    character_id: str,
    *,
    limit: int = 3,
) -> list[KnowledgeChunk]:
    return list(
        db.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.character_id == character_id)
            .order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.id.desc())
            .limit(limit)
        )
    )


def count_character_chunks(db: Session, character_id: str) -> int:
    return len(
        list(
            db.scalars(
                select(KnowledgeChunk.id).where(
                    KnowledgeChunk.character_id == character_id
                )
            )
        )
    )
