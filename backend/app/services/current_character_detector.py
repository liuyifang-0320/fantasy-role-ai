import re
from pathlib import Path

from app.services.candidate_noise_classifier import classify_candidate_name, normalize_candidate_name


IDENTITY_PATTERNS = [
    (r"(?:你是|我是|你的角色是|角色[:：]|角色名[:：]|姓名[:：])\s*([\u4e00-\u9fff]{2,5})", "identity_field"),
]


def detect_current_character(filename: str, clean_text: str, segments: list[dict] | None = None) -> dict[str, object]:
    evidence: list[str] = []
    filename_name = name_from_filename(filename)
    if filename_name:
        evidence.append(f"filename: {filename}")
        return {
            "current_character_name": filename_name,
            "confidence": 0.82,
            "evidence": evidence,
            "source": "filename",
        }

    head = "\n".join((clean_text or "").splitlines()[:20])
    for pattern, source in IDENTITY_PATTERNS:
        match = re.search(pattern, head)
        if not match:
            continue
        name = normalize_candidate_name(match.group(1))
        if classify_candidate_name(name, ["identity_field"]) == "person":
            evidence.append(match.group(0)[:120])
            return {
                "current_character_name": name,
                "confidence": 0.9,
                "evidence": evidence,
                "source": source,
            }

    title = first_title_line(clean_text)
    if title:
        possible = normalize_candidate_name(title)
        if classify_candidate_name(possible, ["title"]) == "person":
            evidence.append(title)
            return {
                "current_character_name": possible,
                "confidence": 0.68,
                "evidence": evidence,
                "source": "title",
            }

    return {
        "current_character_name": "",
        "confidence": 0.0,
        "evidence": [],
        "source": "none",
    }


def name_from_filename(filename: str) -> str:
    stem = Path(filename or "").stem
    stem = re.sub(r"(角色本|个人本|剧本|资料|扫描|OCR|第[一二三四五六七八九十0-9]+[幕章]).*", "", stem)
    candidates = re.findall(r"[\u4e00-\u9fff]{2,5}", stem)
    for candidate in candidates:
        clean = normalize_candidate_name(candidate)
        if classify_candidate_name(clean, ["filename"]) == "person":
            return clean
    return ""


def first_title_line(text: str) -> str:
    for line in (text or "").splitlines()[:10]:
        stripped = line.strip(" #\t")
        if 2 <= len(stripped) <= 8 and "：" not in stripped and ":" not in stripped:
            return stripped
    return ""
