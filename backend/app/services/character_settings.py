from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Character, CharacterSettings
from app.services.ids import next_prefixed_id


TONE_LABELS = {
    "gentle": "温柔",
    "cold": "清冷克制",
    "playful": "俏皮",
    "mature": "成熟姐姐",
    "yandere_light": "轻病娇",
    "poetic": "诗意克制",
    "original": "遵循原角色",
}
REPLY_LENGTH_LABELS = {
    "short": "短回复",
    "medium": "中等",
    "long": "稍长",
}
INTIMACY_LABELS = {
    "low": "低亲密",
    "normal": "正常",
    "high": "高亲密",
}
PET_POSITION_LABELS = {
    "bottom_right": "右下角",
    "bottom_left": "左下角",
    "floating": "悬浮",
}


def get_settings(db: Session, character_id: str) -> CharacterSettings | None:
    return db.scalar(
        select(CharacterSettings).where(CharacterSettings.character_id == character_id)
    )


def get_or_create_settings(
    db: Session,
    character: Character,
) -> CharacterSettings:
    settings = get_settings(db, character.character_id)
    if settings:
        if settings.user_id is None and character.user_id:
            settings.user_id = character.user_id
            db.flush()
        return settings

    settings = CharacterSettings(
        settings_id=next_prefixed_id(db, CharacterSettings, "settings"),
        user_id=character.user_id,
        project_id=character.project_id,
        character_id=character.character_id,
        **default_settings_values(character),
    )
    db.add(settings)
    db.flush()
    return settings


def update_settings(
    db: Session,
    character: Character,
    payload,
) -> CharacterSettings:
    settings = get_or_create_settings(db, character)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is not None and isinstance(value, str):
            value = value.strip()
        setattr(settings, field, value)
    settings.updated_at = datetime.utcnow()
    db.flush()
    return settings


def reset_settings(db: Session, character: Character) -> CharacterSettings:
    settings = get_or_create_settings(db, character)
    for field, value in default_settings_values(character).items():
        setattr(settings, field, value)
    settings.updated_at = datetime.utcnow()
    db.flush()
    return settings


def default_settings_values(character: Character) -> dict[str, str | bool]:
    return {
        "display_name": character.character_name,
        "user_persona_name": character.user_persona_name,
        "nickname_for_user": character.user_persona_name,
        "relationship_with_user": character.relationship_with_user,
        "relationship_stage": character.relationship_stage,
        "tone_style": "original",
        "reply_length": "medium",
        "intimacy_mode": "normal",
        "spoiler_mode": "non_spoiler",
        "spoiler_protection": True,
        "pet_enabled": True,
        "pet_position": "bottom_right",
        "personality_override": "",
        "speaking_style_override": "",
        "custom_prompt_notes": "",
        "forbidden_topics": "",
    }


def build_settings_prompt(settings: CharacterSettings | None) -> str:
    if not settings:
        return "角色调教配置：未启用额外配置。"

    lines = [
        "角色调教配置（Prompt-level customization，不是真正模型训练）：",
        f"- 角色显示名：{settings.display_name or '沿用原角色名'}",
        f"- 用户扮演身份：{settings.user_persona_name or '沿用原设定'}",
        f"- 对用户的称呼：{settings.nickname_for_user or '自然称呼'}",
        f"- 关系设定：{settings.relationship_with_user or '沿用原关系'}",
        f"- 关系阶段：{settings.relationship_stage or '沿用原阶段'}",
        f"- 语气风格：{TONE_LABELS.get(settings.tone_style, settings.tone_style)}",
        f"- 回复长度偏好：{REPLY_LENGTH_LABELS.get(settings.reply_length, settings.reply_length)}",
        f"- 亲密模式：{INTIMACY_LABELS.get(settings.intimacy_mode, settings.intimacy_mode)}",
        f"- 剧透模式：{settings.spoiler_mode or 'non_spoiler'}",
        (
            "- 剧透保护：开启。涉及真相、凶手、核心秘密时必须保留悬念。"
            if settings.spoiler_protection
            else "- 剧透保护：关闭。但仍不得编造未上传资料中的关键真相。"
        ),
        f"- Q版桌宠：{'开启' if settings.pet_enabled else '关闭'}，位置：{PET_POSITION_LABELS.get(settings.pet_position, settings.pet_position)}",
    ]
    optional_lines = [
        ("性格微调", settings.personality_override),
        ("说话风格微调", settings.speaking_style_override),
        ("用户补充设定", settings.custom_prompt_notes),
        ("禁止话题", settings.forbidden_topics),
    ]
    for label, value in optional_lines:
        if value and value.strip():
            lines.append(f"- {label}：{value.strip()}")
    lines.extend(
        [
            "- 优先尊重这些调教配置，但不能违反剧本设定和防剧透规则。",
            "- 不要主动提到“我是按配置回复的”。",
            "- 如果用户触及禁止话题，应温和回避并把话题带回角色关系或当前剧情。",
        ]
    )
    return "\n".join(lines)


def settings_prompt_preview(settings: CharacterSettings | None, *, limit: int = 600) -> str:
    return build_settings_prompt(settings)[:limit]
