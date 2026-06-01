import re

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import ParsedDocument, ScriptSegment
from app.services.ids import next_prefixed_id


TRUTH_MARKERS = ("真相", "复盘", "凶手", "隐藏身份", "最终任务", "结局", "第六幕")
INSTRUCTION_MARKERS = ("你的任务", "玩家行动", "请你", "你需要", "你的目标")
CLUE_MARKERS = ("线索卡", "线索", "搜证", "证据")
HOST_MARKERS = ("主持人", "DM提示", "主持提示", "给DM")
RELATION_MARKERS = ("情侣", "恋人", "朋友", "宿敌", "暗恋", "旧识", "喜欢")


def build_script_segments(
    db: Session,
    parsed_document: ParsedDocument,
    *,
    clean_text: str,
    current_character_name: str = "",
) -> list[ScriptSegment]:
    db.execute(
        delete(ScriptSegment).where(
            ScriptSegment.parsed_document_id == parsed_document.parsed_id
        )
    )
    blocks = split_blocks(clean_text)
    segments: list[ScriptSegment] = []
    offset = 0
    for index, block in enumerate(blocks, start=1):
        segment_type, visibility, spoiler_level, confidence = classify_segment(
            block,
            parsed_document.filename,
            current_character_name=current_character_name,
        )
        title = detect_title(block) or f"segment-{index}"
        start_offset = clean_text.find(block, offset)
        if start_offset < 0:
            start_offset = offset
        end_offset = start_offset + len(block)
        segment = ScriptSegment(
            segment_id=next_prefixed_id(db, ScriptSegment, "segment"),
            user_id=parsed_document.user_id,
            project_id=parsed_document.project_id or "",
            parsed_document_id=parsed_document.parsed_id,
            segment_type=segment_type,
            title=title[:255],
            content=block,
            clean_content=block,
            start_offset=start_offset,
            end_offset=end_offset,
            visibility=visibility,
            spoiler_level=spoiler_level,
            confidence=confidence,
            source_filename=parsed_document.filename,
        )
        db.add(segment)
        db.flush()
        segments.append(segment)
        offset = end_offset
    return segments


def split_blocks(clean_text: str) -> list[str]:
    raw_blocks = [block.strip() for block in re.split(r"\n\s*\n", clean_text or "") if block.strip()]
    if not raw_blocks and clean_text.strip():
        raw_blocks = [clean_text.strip()]
    blocks: list[str] = []
    for block in raw_blocks:
        if len(block) <= 900:
            blocks.append(block)
            continue
        lines = block.splitlines()
        current = ""
        for line in lines:
            candidate = f"{current}\n{line}".strip() if current else line
            if len(candidate) <= 900:
                current = candidate
            else:
                if current:
                    blocks.append(current)
                current = line
        if current:
            blocks.append(current)
    return blocks


def classify_segment(
    text: str,
    filename: str,
    *,
    current_character_name: str = "",
) -> tuple[str, str, str, float]:
    joined = f"{filename}\n{text}"
    if any(marker in joined for marker in TRUTH_MARKERS):
        return "truth_reveal", "restricted", "heavy", 0.86
    if any(marker in joined for marker in HOST_MARKERS):
        return "host_guide", "restricted", "mild", 0.78
    if any(marker in joined for marker in INSTRUCTION_MARKERS):
        return "player_instruction", "self_only", "mild", 0.72
    if any(marker in joined for marker in CLUE_MARKERS):
        return "clue", "public", "mild", 0.7
    if any(marker in joined for marker in RELATION_MARKERS):
        return "relationship_info", "public", "none", 0.68
    if re.search(r"(?m)^[\u4e00-\u9fff]{2,5}[:：]", text):
        return "dialogue", "public", "none", 0.72
    if current_character_name:
        return "current_character_book", "self_only", "none", 0.76
    if "角色本" in filename or "个人本" in filename:
        return "character_book", "self_only", "none", 0.7
    return "unknown", "public", "none", 0.42


def detect_title(block: str) -> str:
    first = (block or "").splitlines()[0].strip()
    if len(first) <= 40:
        return first
    return ""
