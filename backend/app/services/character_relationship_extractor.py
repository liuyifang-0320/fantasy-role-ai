import re
from collections import defaultdict

from app.models import CharacterCandidate, ParsedDocument
from app.services.personhood_validator import is_strict_relationship_name, validate_person_candidate


RELATION_TYPES = (
    "情侣",
    "朋友",
    "宿敌",
    "兄妹",
    "父女",
    "母女",
    "同学",
    "恋人",
    "暗恋",
    "旧识",
)
SYMMETRIC_RELATION_TYPES = {
    "情侣",
    "恋人",
    "朋友",
    "宿敌",
    "兄妹",
    "父女",
    "母女",
    "同学",
    "旧识",
    "分别",
    "重逢",
    "认识",
}
STOP_NAMES = {
    "第一幕",
    "第二幕",
    "第三幕",
    "Chapter",
    "线索",
    "真相",
    "凶手",
    "证据",
    "旧街区",
    "神社",
    "项目",
    "用户",
    "角色",
    "姓名",
    "主持人",
    "玩家",
    "资料",
    "文档",
    "任务",
    "行动",
    "结局",
    "复盘",
    "日记",
    "照片",
    "声音",
}
KINSHIP_MAP = {
    "父亲": "父亲",
    "母亲": "母亲",
    "女儿": "女儿",
    "儿子": "儿子",
    "朋友": "朋友",
    "恋人": "恋人",
}


def extract_character_relationships(
    project_id: str,
    parsed_documents: list[ParsedDocument],
    character_candidates: list[CharacterCandidate] | None = None,
) -> list[dict[str, str | float | list[str]]]:
    known_names = {
        candidate.name
        for candidate in (character_candidates or [])
        if candidate.name and is_valid_name(candidate.name)
    }
    relationship_by_key: dict[
        tuple[str, str, str, str],
        dict[str, str | float | list[str]],
    ] = {}

    for document in parsed_documents:
        text = document.raw_text or ""
        if not text.strip():
            continue
        for item in extract_relationships_from_text(text):
            source = str(item["source_character_name"])
            target = str(item["target_character_name"])
            relation_type = str(item["relation_type"])
            if not is_valid_name(source) or not is_valid_name(target):
                continue
            key = relationship_key(project_id, source, target, relation_type)
            existing = relationship_by_key.get(key)
            if existing:
                existing["evidence"] = merge_text(
                    str(existing["evidence"]),
                    str(item["evidence"]),
                )
                existing["source_document_ids"] = merge_list(
                    existing["source_document_ids"],
                    [document.parsed_id],
                )
                existing["confidence"] = max(
                    float(existing["confidence"]),
                    float(item["confidence"]),
                )
                continue

            relationship_by_key[key] = {
                "project_id": project_id,
                "source_character_name": source,
                "target_character_name": target,
                "relation_type": relation_type,
                "relation_summary": str(item["relation_summary"])[:200],
                "evidence": str(item["evidence"])[:500],
                "source_document_ids": [document.parsed_id],
                "confidence": float(item["confidence"]),
            }
            if source in known_names or target in known_names:
                relationship_by_key[key]["confidence"] = min(
                    1.0,
                    float(relationship_by_key[key]["confidence"]) + 0.06,
                )

    return list(relationship_by_key.values())


def extract_relationships_from_text(text: str) -> list[dict[str, str | float]]:
    results: list[dict[str, str | float]] = []
    relation_words = "|".join(map(re.escape, RELATION_TYPES))

    patterns = [
        (
            rf"([\u4e00-\u9fff]{{2,5}})[和与]([\u4e00-\u9fff]{{2,5}})是({relation_words})",
            lambda m: (m.group(1), m.group(2), m.group(3), f"{m.group(1)}和{m.group(2)}是{m.group(3)}", 0.92),
        ),
        (
            r"([\u4e00-\u9fff]{2,5})(喜欢|爱|暗恋|讨厌|恨|认识)([\u4e00-\u9fff]{2,5})",
            lambda m: (m.group(1), m.group(3), normalize_action_relation(m.group(2)), f"{m.group(1)}{m.group(2)}{m.group(3)}", 0.86),
        ),
        (
            r"([\u4e00-\u9fff]{2,5})曾经[和与]([\u4e00-\u9fff]{2,5})(分别|重逢)",
            lambda m: (m.group(1), m.group(2), m.group(3), f"{m.group(1)}曾经和{m.group(2)}{m.group(3)}", 0.78),
        ),
        (
            r"([\u4e00-\u9fff]{2,5})是([\u4e00-\u9fff]{2,5})的(父亲|母亲|女儿|儿子|朋友|恋人)",
            lambda m: (m.group(1), m.group(2), KINSHIP_MAP.get(m.group(3), "未知"), f"{m.group(1)}是{m.group(2)}的{m.group(3)}", 0.82),
        ),
    ]

    for pattern, builder in patterns:
        for match in re.finditer(pattern, text):
            source, target, relation_type, summary, confidence = builder(match)
            source = clean_relationship_name(str(source))
            target = clean_relationship_name(str(target))
            if source == target:
                continue
            if not is_valid_name(source) or not is_valid_name(target):
                continue
            results.append(
                {
                    "source_character_name": source,
                    "target_character_name": target,
                    "relation_type": relation_type,
                    "relation_summary": summary,
                    "evidence": build_evidence(text, match.start(), match.end()),
                    "confidence": confidence,
                }
            )
    return results


def normalize_action_relation(action: str) -> str:
    if action == "爱":
        return "恋人"
    if action in {"讨厌", "恨"}:
        return "宿敌"
    return action


def relationship_key(
    project_id: str,
    source: str,
    target: str,
    relation_type: str,
) -> tuple[str, str, str, str]:
    if relation_type in SYMMETRIC_RELATION_TYPES:
        left, right = sorted([source, target])
        return project_id, left, right, relation_type
    return project_id, source, target, relation_type


def is_valid_name(name: str) -> bool:
    name = clean_relationship_name(name)
    if not (2 <= len(name) <= 5):
        return False
    if name in STOP_NAMES:
        return False
    if any(stop in name for stop in STOP_NAMES):
        return False
    validation = validate_person_candidate({"name": name, "source_types": ["relationship_sentence"]})
    if validation["candidate_type"] in {"noise", "document_term", "structure_term", "abstract", "action_phrase", "prop", "place"}:
        return False
    return bool(re.fullmatch(r"[\u4e00-\u9fff]{2,5}", name)) and is_strict_relationship_name(name)


def clean_relationship_name(name: str) -> str:
    return re.sub(r"\s+", "", (name or "").strip("锛?銆愩€戙€娿€嬨€屻€嶁€溾€漒\"' "))


def build_evidence(text: str, start: int, end: int, limit: int = 160) -> str:
    left = max(0, start - 50)
    right = min(len(text), end + 90)
    return " ".join(text[left:right].split())[:limit]


def merge_list(existing: object, new_values: list[str]) -> list[str]:
    values: list[str] = []
    for item in [*(existing if isinstance(existing, list) else []), *new_values]:
        if item and item not in values:
            values.append(item)
    return values


def merge_text(existing: str, new: str, *, limit: int = 500) -> str:
    parts = []
    for item in [existing.strip(), new.strip()]:
        if item and item not in parts:
            parts.append(item)
    return "；".join(parts)[:limit]
