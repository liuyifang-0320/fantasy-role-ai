import re

from app.services.personhood_validator import validate_person_candidate


STRUCTURE_TERMS = {
    "序章",
    "终章",
    "第一幕",
    "第二幕",
    "第三幕",
    "第四幕",
    "第五幕",
    "第六幕",
}
DOCUMENT_TERMS = {"资料", "文档", "文件", "页面", "图片", "扫描", "附录", "角色本", "个人本"}
MECHANISM_TERMS = {"主持人", "玩家", "DM", "NPC", "角色", "人物", "剧本", "作者"}
CLUE_TERMS = {"线索", "真相", "复盘", "任务", "行动", "结局", "证据", "凶手信息", "凶手"}
PROP_TERMS = {"房间", "手机", "照片", "日记", "笔记", "钥匙", "信件", "声音", "回忆", "手", "眼神"}
PLACE_TERMS = {"学校", "公司", "神社", "医院", "旧街区", "房间", "街区", "仓库", "教室"}
ORG_SUFFIXES = ("公司", "协会", "学校", "医院", "组织", "集团")


def classify_candidate_name(name: str, source_types: list[str] | None = None) -> str:
    clean_name = normalize_candidate_name(name)
    source_types = source_types or []
    validation = validate_person_candidate({"name": clean_name, "source_types": source_types})
    if validation["candidate_type"] in {
        "abstract",
        "action_phrase",
        "document_term",
        "structure_term",
        "noise",
        "prop",
        "place",
    }:
        return str(validation["candidate_type"])
    if not clean_name:
        return "noise"
    if re.fullmatch(r"第[一二三四五六七八九十0-9]+[幕章]", clean_name) or re.fullmatch(
        r"Chapter\s*\d+",
        clean_name,
        re.IGNORECASE,
    ):
        return "structure_term"
    if clean_name in STRUCTURE_TERMS:
        return "structure_term"
    if clean_name in DOCUMENT_TERMS or any(term in clean_name for term in DOCUMENT_TERMS):
        return "document_term"
    if clean_name in MECHANISM_TERMS:
        return "document_term"
    if clean_name in CLUE_TERMS or any(term == clean_name for term in CLUE_TERMS):
        return "clue"
    if clean_name in PROP_TERMS:
        return "prop"
    if clean_name in PLACE_TERMS:
        return "place"
    if clean_name.endswith(ORG_SUFFIXES):
        return "organization"
    if "的" in clean_name:
        return "prop"
    if not re.fullmatch(r"[\u4e00-\u9fff]{2,5}", clean_name):
        return "noise"
    if set(source_types) & {
        "filename",
        "title",
        "current_character",
        "dialogue_label",
        "identity_field",
    }:
        return "person"
    if "relationship_sentence" in set(source_types):
        return "person"
    return "unknown"


def normalize_candidate_name(name: str) -> str:
    return re.sub(r"\s+", "", (name or "").strip("：:【】《》「」“”\"' "))


def is_non_person_type(candidate_type: str) -> bool:
    return candidate_type in {
        "organization",
        "place",
        "prop",
        "clue",
        "document_term",
        "structure_term",
        "abstract",
        "action_phrase",
        "noise",
    }
