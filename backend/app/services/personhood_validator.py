import re


PRONOUNS = {"我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们"}
PRONOUN_PREFIXES = ("我", "你", "他", "她", "它")
PRONOUN_PHRASE_MARKERS = (
    "依然",
    "知道",
    "已经",
    "开始",
    "一直",
    "曾经",
    "现在",
    "后来",
    "因为",
    "所以",
    "如果",
    "但是",
    "什么",
    "怎么",
    "为什么",
)
ABSTRACT_TERMS = {
    "哲理",
    "命运",
    "时间",
    "回忆",
    "真相",
    "线索",
    "关系",
    "任务",
    "记忆",
    "秘密",
    "爱情",
    "故事",
    "结局",
    "复盘",
    "凶手",
    "凶手信息",
    "世界观",
    "设定",
}
EMOTION_TERMS = {"自信", "悲伤", "愤怒", "孤独", "温柔", "难过", "疲惫", "痛苦"}
STRUCTURE_TERMS = {
    "序章",
    "终章",
    "第一幕",
    "第二幕",
    "第三幕",
    "第四幕",
    "第五幕",
    "第六幕",
    "第一章",
    "第二章",
    "第三章",
    "第四章",
    "第五章",
    "第六章",
    "主持人",
    "玩家",
    "资料",
    "文档",
    "文件",
    "页面",
    "剧本",
    "角色",
    "人物",
}
PROP_OR_PLACE_TERMS = {
    "照片",
    "日记",
    "声音",
    "房间",
    "学校",
    "公司",
    "城市",
    "医院",
    "神社",
    "线索卡",
    "手机",
    "笔记",
    "钥匙",
    "证据",
}
ACTION_OR_ADVERB_TERMS = {
    "依然",
    "始终",
    "一直",
    "曾经",
    "现在",
    "后来",
    "开始",
    "出现",
    "离开",
    "知道",
    "相信",
    "忘记",
    "看见",
    "听见",
    "不是",
    "没有",
    "仍然",
    "忽然",
    "突然",
}
NON_PERSON_SUFFIXES = ("城市", "之子", "信息", "主义", "规则", "提示", "资料")
ROLE_CATEGORY_TERMS = {"孤儿", "少女", "少年", "男人", "女人", "老人", "孩子", "医生", "警察", "老师", "学生"}
PHRASE_FRAGMENT_MARKERS = ("不", "没", "会", "能", "想", "要", "该", "仍", "依然", "知道", "记得")
PUNCTUATION_RE = re.compile(r"[，。！？、；：“”‘’《》【】（）()\[\],.!?;:]")


def validate_person_candidate(candidate: str | dict, evidence: object | None = None) -> dict[str, object]:
    """Classify whether a candidate looks like a playable person character."""

    name = extract_name(candidate)
    source_types = extract_source_types(candidate)
    reason = ""
    candidate_type = "unknown"
    likely_person = False
    confidence_level = "low"

    if not name:
        return result(False, "noise", "low", "候选为空")
    if PUNCTUATION_RE.search(name) or not re.fullmatch(r"[\u4e00-\u9fff]{2,5}", name):
        return result(False, "noise", "low", "候选包含标点、非中文或长度不合理")
    if name in PRONOUNS:
        return result(False, "noise", "low", "第一/第二/第三人称代词不是角色名")
    if starts_with_pronoun_phrase(name):
        return result(False, "action_phrase", "low", "含代词的动作/状态短语不是角色名")
    if name in ABSTRACT_TERMS:
        return result(False, "abstract", "low", "抽象名词不是角色名")
    if name in EMOTION_TERMS:
        return result(False, "abstract", "low", "情绪或状态词不是角色名")
    if name in STRUCTURE_TERMS or is_chapter_term(name):
        return result(False, "structure_term", "low", "章节、机制或文档结构词不是角色名")
    if name in ROLE_CATEGORY_TERMS:
        return result(False, "document_term", "low", "通用身份类别词不是具体角色名")
    if name in PROP_OR_PLACE_TERMS:
        return result(False, classify_prop_or_place(name), "low", "道具、地点或资料词不是角色名")
    if any(term in name for term in ABSTRACT_TERMS | EMOTION_TERMS | STRUCTURE_TERMS):
        return result(False, "abstract", "low", "候选包含抽象/结构词")
    if "的" in name:
        return result(False, "prop", "low", "X的Y 结构应归属 X 的证据，不生成独立人物")
    if any(name.endswith(suffix) for suffix in NON_PERSON_SUFFIXES):
        return result(False, "document_term", "low", "候选后缀更像文档、地点或概念")
    if name in ACTION_OR_ADVERB_TERMS or any(name.startswith(term) for term in ACTION_OR_ADVERB_TERMS):
        return result(False, "action_phrase", "low", "动作、副词或状态短语不是角色名")
    if looks_like_phrase_fragment(name):
        return result(False, "action_phrase", "low", "候选更像从句片段，不是稳定人物名")

    strong_sources = {"current_character", "filename", "title", "identity_field", "llm_review"}
    source_set = set(source_types)
    dialogue_count = int(get_value(candidate, "dialogue_count", 0) or 0)
    has_dialogue = "dialogue_label" in source_set and (
        dialogue_count >= 2
        or bool((source_set - {"dialogue_label", "relationship_sentence"}))
        or "relationship_sentence" in source_set
    )
    if source_set & strong_sources or has_dialogue:
        candidate_type = "person"
        likely_person = True
        confidence_level = "high"
        reason = "具备强人物证据"
    elif "dialogue_label" in source_set:
        candidate_type = "person"
        likely_person = True
        confidence_level = "medium"
        reason = "仅单次对白标签，需更多证据或用户确认"
    elif "relationship_sentence" in source_set or "repeated_subject" in source_set:
        candidate_type = "person"
        likely_person = True
        confidence_level = "medium"
        reason = "仅关系句/复现主体证据，不能直接升为高置信"
    else:
        reason = "缺少强人物证据"

    return result(likely_person, candidate_type, confidence_level, reason)


def is_strict_relationship_name(name: str) -> bool:
    validation = validate_person_candidate({"name": name, "source_types": ["relationship_sentence"]})
    if validation["candidate_type"] in {"noise", "document_term", "structure_term", "abstract", "action_phrase"}:
        return False
    if str(validation["reason"]).startswith("候选包含"):
        return False
    return bool(re.fullmatch(r"[\u4e00-\u9fff]{2,5}", name or ""))


def result(
    is_likely_person: bool,
    candidate_type: str,
    confidence_level: str,
    reason: str,
) -> dict[str, object]:
    return {
        "is_likely_person": is_likely_person,
        "candidate_type": candidate_type,
        "confidence_level": confidence_level,
        "reason": reason,
    }


def extract_name(candidate: str | dict) -> str:
    if isinstance(candidate, str):
        return candidate.strip()
    return str(
        candidate.get("canonical_name")
        or candidate.get("name")
        or candidate.get("display_name")
        or ""
    ).strip()


def extract_source_types(candidate: str | dict) -> list[str]:
    if not isinstance(candidate, dict):
        return []
    value = candidate.get("source_types") or []
    return [str(item) for item in value] if isinstance(value, list) else []


def get_value(candidate: str | dict, key: str, default: object = None) -> object:
    if isinstance(candidate, dict):
        return candidate.get(key, default)
    return default


def starts_with_pronoun_phrase(name: str) -> bool:
    if not name.startswith(PRONOUN_PREFIXES):
        return False
    return any(marker in name for marker in PRONOUN_PHRASE_MARKERS) or len(name) >= 3


def is_chapter_term(name: str) -> bool:
    return bool(
        re.fullmatch(r"第[一二三四五六七八九十0-9]+[幕章]", name)
        or re.fullmatch(r"Chapter\s*\d+", name, re.IGNORECASE)
    )


def looks_like_phrase_fragment(name: str) -> bool:
    if len(name) < 3:
        return False
    if any(marker in name[1:] for marker in PHRASE_FRAGMENT_MARKERS):
        return True
    return False


def classify_prop_or_place(name: str) -> str:
    if name in {"学校", "公司", "城市", "医院", "神社", "房间"}:
        return "place"
    return "prop"
