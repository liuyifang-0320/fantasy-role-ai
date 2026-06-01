import re

from app.models import Character


QUESTION_MARKERS = ("吗", "什么", "是不是", "知道", "记得", "？", "?")
NAME_INSTRUCTION_MARKERS = ("以后叫我", "你可以叫我", "我的名字是")


def extract_memory_candidates(
    *,
    character: Character,
    user_message: str,
    assistant_reply: str,
    pet_action: str,
    session_id: str,
) -> list[dict[str, str | int | bool]]:
    message = " ".join(user_message.strip().split())
    if not message:
        return []

    candidates: list[dict[str, str | int | bool]] = []
    preference_question = is_preference_question(message)
    if not preference_question:
        candidates.extend(extract_preference_candidates(message))
    candidates.extend(extract_emotional_state_candidates(message))
    candidates.extend(extract_name_candidates(message))
    if not preference_question:
        candidates.extend(extract_relationship_candidates(message, character))
    return dedupe_candidates(candidates)


def extract_preference_candidates(message: str) -> list[dict[str, str | int | bool]]:
    if is_preference_question(message) or has_name_instruction(message):
        return []

    patterns = [
        (r"我喜欢(.{1,40})", "用户喜欢{value}。", "用户明确陈述偏好"),
        (r"我讨厌(.{1,40})", "用户讨厌{value}。", "用户明确陈述反向偏好"),
        (r"我不喜欢(.{1,40})", "用户不喜欢{value}。", "用户明确陈述反向偏好"),
        (r"我希望(.{1,40})", "用户希望{value}。", "用户明确陈述偏好或期待"),
        (r"我想要(.{1,40})", "用户想要{value}。", "用户明确陈述偏好或需求"),
    ]
    candidates: list[dict[str, str | int | bool]] = []
    for pattern, template, reason in patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        value = clean_memory_value(match.group(1))
        if value:
            candidates.append(
                build_candidate(
                    memory_type="user_preference",
                    content=template.format(value=value),
                    importance=3,
                    reason=reason,
                )
            )
    return candidates


def is_preference_question(message: str) -> bool:
    compact = "".join(message.split())
    if not any(marker in compact for marker in QUESTION_MARKERS):
        return False
    question_patterns = (
        r"(?:你.*(?:记得|知道).*我.*喜欢.*(?:什么|吗|[？?]))",
        r"我喜欢什么",
        r"我是不是.*喜欢",
        r"我喜欢.{0,20}(?:吗|[？?])$",
        r"我(?:希望|想要).{0,30}(?:吗|[？?])$",
    )
    return any(re.search(pattern, compact) for pattern in question_patterns)


def has_name_instruction(message: str) -> bool:
    return any(marker in message for marker in NAME_INSTRUCTION_MARKERS)


def extract_emotional_state_candidates(message: str) -> list[dict[str, str | int | bool]]:
    emotion_markers = ("难过", "很累", "想哭", "不开心")
    if not any(marker in message for marker in emotion_markers):
        return []
    return [
        build_candidate(
            memory_type="emotional_state",
            content=f"用户曾表达当前状态：{message[:60]}",
            importance=4,
            reason="用户表达了需要被照顾的情绪状态",
        )
    ]


def extract_name_candidates(message: str) -> list[dict[str, str | int | bool]]:
    patterns = [rf"{marker}(.{{1,20}})" for marker in NAME_INSTRUCTION_MARKERS]
    for pattern in patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        name = clean_memory_value(match.group(1))
        if name:
            return [
                build_candidate(
                    memory_type="user_preference",
                    content=f"用户希望被称呼为{name}。",
                    importance=4,
                    reason="用户明确指定称呼",
                )
            ]
    return []


def extract_relationship_candidates(
    message: str,
    character: Character,
) -> list[dict[str, str | int | bool]]:
    relationship_markers = ("我们", "你还记得", "上次", "约定", "答应")
    if not any(marker in message for marker in relationship_markers):
        return []
    memory_type = (
        "relationship"
        if any(marker in message for marker in ("我们", "你还记得"))
        else "story_interaction"
    )
    return [
        build_candidate(
            memory_type=memory_type,
            content=f"用户和{character.character_name}提到过：{message[:60]}",
            importance=3,
            reason="用户提到关系连续性或剧情互动",
        )
    ]


def build_candidate(
    *,
    memory_type: str,
    content: str,
    importance: int,
    reason: str,
) -> dict[str, str | int | bool]:
    return {
        "memory_type": memory_type,
        "content": " ".join(content.split()),
        "importance": importance,
        "reason": reason,
        "saved": False,
    }


def clean_memory_value(value: str) -> str:
    cleaned = re.split(r"[。！!？?，,；;]", value.strip())[0].strip()
    return cleaned[:40]


def dedupe_candidates(
    candidates: list[dict[str, str | int | bool]],
) -> list[dict[str, str | int | bool]]:
    seen: set[str] = set()
    deduped: list[dict[str, str | int | bool]] = []
    for candidate in candidates:
        content = str(candidate["content"])
        if content in seen:
            continue
        seen.add(content)
        deduped.append(candidate)
    return deduped
