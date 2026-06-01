import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CharacterProfile, ParsedDocument
from app.services.ids import next_prefixed_id
from app.services.parser import build_preview


KEYWORDS = ("情侣", "恋人", "喜欢", "爱", "分别", "重逢", "秘密", "凶手", "神社", "旧街区")
SPOILER_GUARDRAILS = [
    "不得主动剧透。",
    "不得编造未上传资料中的关键真相。",
]
DEFAULT_HIDDEN_SECRETS = ["当前无法确认，默认不主动暴露剧本核心秘密。"]


def create_character_profile(
    db: Session,
    parsed_documents: list[ParsedDocument],
    target_character_name: str,
    user_persona_name: str,
    relationship_hint: str,
    character_id: str | None = None,
    project_id: str | None = None,
    user_id: str | None = None,
) -> CharacterProfile:
    merged_text = "\n\n".join(
        parsed_document.raw_text
        for parsed_document in parsed_documents
        if parsed_document.raw_text
    )
    extracted = extract_profile_data(
        merged_text,
        target_character_name=target_character_name.strip(),
        user_persona_name=user_persona_name.strip(),
        relationship_hint=relationship_hint.strip(),
    )
    profile = CharacterProfile(
        profile_id=next_prefixed_id(db, CharacterProfile, "profile"),
        user_id=user_id,
        project_id=project_id,
        character_id=character_id,
        parsed_document_id=parsed_documents[0].parsed_id if parsed_documents else None,
        target_character_name=target_character_name.strip(),
        user_persona_name=user_persona_name.strip(),
        relationship_hint=relationship_hint.strip(),
        **extracted,
    )
    db.add(profile)
    db.flush()
    return profile


def extract_profile_data(
    raw_text: str,
    target_character_name: str,
    user_persona_name: str,
    relationship_hint: str,
) -> dict[str, str]:
    compact_text = " ".join(raw_text.split())
    matched_keywords = [keyword for keyword in KEYWORDS if keyword in compact_text]
    has_target_character = bool(target_character_name and target_character_name in compact_text)
    has_user_persona = bool(user_persona_name and user_persona_name in compact_text)
    source_preview = build_preview(raw_text)

    has_rule_signal = bool(has_target_character or has_user_persona or matched_keywords)
    extraction_status = "success" if compact_text and has_rule_signal else "mock"

    if has_target_character:
        identity = build_identity(matched_keywords)
    else:
        identity = "由剧本资料生成的关键角色"

    personality = build_personality(matched_keywords)
    speaking_style = build_speaking_style(matched_keywords)
    background_summary = build_background_summary(
        target_character_name,
        matched_keywords,
        source_preview,
    )
    relationship_summary = build_relationship_summary(
        target_character_name,
        user_persona_name,
        relationship_hint,
        has_target_character,
        has_user_persona,
    )
    story_stage = build_story_stage(matched_keywords)
    known_facts = extract_known_facts(source_preview)

    return {
        "extracted_identity": identity,
        "extracted_personality": personality,
        "speaking_style": speaking_style,
        "background_summary": background_summary,
        "relationship_summary": relationship_summary,
        "story_stage": story_stage,
        "known_facts": json.dumps(known_facts, ensure_ascii=False),
        "hidden_secrets": json.dumps(DEFAULT_HIDDEN_SECRETS, ensure_ascii=False),
        "spoiler_guardrails": json.dumps(SPOILER_GUARDRAILS, ensure_ascii=False),
        "source_preview": source_preview,
        "extraction_status": extraction_status,
    }


def build_identity(matched_keywords: list[str]) -> str:
    if "神社" in matched_keywords:
        return "与神社旧事相关的关键角色"
    if "旧街区" in matched_keywords:
        return "旧街区叙事中的关键角色"
    return "剧本资料中的关键角色"


def build_personality(matched_keywords: list[str]) -> str:
    if any(keyword in matched_keywords for keyword in ("秘密", "凶手")):
        return "克制、谨慎、藏着秘密"
    if any(keyword in matched_keywords for keyword in ("喜欢", "爱", "分别", "重逢")):
        return "温柔、敏感、带有故事感"
    return "温柔、敏感、带有故事感"


def build_speaking_style(matched_keywords: list[str]) -> str:
    if any(keyword in matched_keywords for keyword in ("秘密", "凶手")):
        return "谨慎、留白、避免直说关键真相"
    return "克制、暧昧、带有回忆感"


def build_background_summary(
    target_character_name: str,
    matched_keywords: list[str],
    source_preview: str,
) -> str:
    if matched_keywords and source_preview:
        tags = "、".join(matched_keywords[:4])
        return (
            f"根据上传资料，{target_character_name}与“{tags}”等剧情线索相关。"
            f"当前摘要：{source_preview[:120]}"
        )
    return "根据上传资料生成的角色背景摘要，当前为规则抽取版本。"


def build_relationship_summary(
    target_character_name: str,
    user_persona_name: str,
    relationship_hint: str,
    has_target_character: bool,
    has_user_persona: bool,
) -> str:
    relationship = relationship_hint or "重要羁绊"
    if has_target_character and has_user_persona:
        return (
            f"{target_character_name}与{user_persona_name}的关系提示为“{relationship}”，"
            "文本中存在两人关系上下文。"
        )
    return f"{target_character_name}与{user_persona_name}的关系暂按“{relationship}”处理。"


def build_story_stage(matched_keywords: list[str]) -> str:
    if "重逢" in matched_keywords:
        return "重逢推进"
    if "分别" in matched_keywords:
        return "分别之后"
    if any(keyword in matched_keywords for keyword in ("情侣", "恋人", "喜欢", "爱")):
        return "情感升温"
    return "初识升温"


def extract_known_facts(source_preview: str) -> list[str]:
    if not source_preview:
        return ["当前资料中暂未抽取到稳定事实。"]

    chunks = [
        chunk.strip(" ，。；;")
        for chunk in re.split(r"[。！？!?；;\n]+", source_preview)
        if chunk.strip(" ，。；;")
    ]
    facts = [chunk[:80] for chunk in chunks[:3]]
    return facts or [source_preview[:80]]


def get_profile(db: Session, profile_id: str) -> CharacterProfile | None:
    return db.scalar(
        select(CharacterProfile).where(CharacterProfile.profile_id == profile_id)
    )


def list_profiles(db: Session, user_id: str | None = None) -> list[CharacterProfile]:
    statement = select(CharacterProfile)
    if user_id:
        statement = statement.where(
            (CharacterProfile.user_id == user_id) | CharacterProfile.user_id.is_(None)
        )
    return list(
        db.scalars(
            statement.order_by(CharacterProfile.created_at.desc())
        )
    )


def get_latest_profile_for_character(
    db: Session,
    character_id: str,
) -> CharacterProfile | None:
    return db.scalar(
        select(CharacterProfile)
        .where(CharacterProfile.character_id == character_id)
        .order_by(CharacterProfile.created_at.desc())
    )


def parse_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []
