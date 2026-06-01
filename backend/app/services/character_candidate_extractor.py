import re
from collections import defaultdict

from app.models import ParsedDocument
from app.services.candidate_llm_reviewer import review_candidates
from app.services.candidate_noise_classifier import classify_candidate_name, normalize_candidate_name
from app.services.character_candidate_merger import merge_candidate_payloads
from app.services.character_relationship_extractor import build_evidence, extract_relationships_from_text
from app.services.current_character_detector import detect_current_character
from app.services.personhood_validator import validate_person_candidate
from app.services.script_text_cleaner import clean_script_text


CandidatePayload = dict[str, str | float | int | bool | list[str]]


def extract_character_candidates(
    project_id: str,
    parsed_documents: list[ParsedDocument],
) -> list[CandidatePayload]:
    accumulator: dict[str, CandidatePayload] = {}
    clean_documents: list[tuple[ParsedDocument, str]] = []

    for document in parsed_documents:
        clean_result = clean_script_text(document.raw_text or "", document.filename)
        clean_text = str(clean_result["clean_text"])
        clean_documents.append((document, clean_text))
        current_detection = detect_current_character(document.filename, clean_text, [])
        current_name = str(current_detection.get("current_character_name") or "")
        if current_name:
            add_evidence(
                accumulator,
                name=current_name,
                source_type="current_character",
                evidence="；".join(str(item) for item in current_detection.get("evidence", [])) or document.filename,
                parsed_id=document.parsed_id,
                confidence=0.9,
            )

        extract_dialogue_labels(accumulator, clean_text, document.parsed_id)
        extract_identity_fields(accumulator, clean_text, document.parsed_id)
        extract_relationship_evidence(accumulator, clean_text, document.parsed_id)
        extract_action_subjects(accumulator, clean_text, document.parsed_id)

    attach_possessive_evidence(accumulator, clean_documents)
    payloads = finalize_candidates(project_id, list(accumulator.values()))
    payloads = merge_candidate_payloads(payloads)
    reviews = review_candidates(project_id, payloads, build_segments_summary(clean_documents), {})
    apply_reviews(payloads, reviews)
    return sorted(
        payloads,
        key=lambda item: (
            str(item.get("candidate_type")) == "person",
            str(item.get("confidence_level")) == "high",
            float(item.get("confidence") or 0),
        ),
        reverse=True,
    )


def extract_dialogue_labels(
    accumulator: dict[str, CandidatePayload],
    text: str,
    parsed_id: str,
) -> None:
    for match in re.finditer(r"(?m)^([\u4e00-\u9fff]{2,5})\s*[:：]", text):
        name = normalize_candidate_name(match.group(1))
        if not is_reasonable_candidate_name(name, ["dialogue_label"]):
            continue
        add_evidence(
            accumulator,
            name=name,
            source_type="dialogue_label",
            evidence=build_evidence(text, match.start(), match.end()),
            parsed_id=parsed_id,
            confidence=0.86,
            dialogue_count=1,
        )


def extract_identity_fields(
    accumulator: dict[str, CandidatePayload],
    text: str,
    parsed_id: str,
) -> None:
    patterns = [
        r"(?:姓名|角色|角色名|玩家)[:：]\s*([\u4e00-\u9fff]{2,5})",
        r"(?:你是|我是|你的角色是)\s*([\u4e00-\u9fff]{2,5})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            name = normalize_candidate_name(match.group(1))
            if not is_reasonable_candidate_name(name, ["identity_field"]):
                continue
            add_evidence(
                accumulator,
                name=name,
                source_type="identity_field",
                evidence=build_evidence(text, match.start(), match.end()),
                parsed_id=parsed_id,
                confidence=0.9,
            )


def extract_relationship_evidence(
    accumulator: dict[str, CandidatePayload],
    text: str,
    parsed_id: str,
) -> None:
    for relationship in extract_relationships_from_text(text):
        source = normalize_candidate_name(str(relationship["source_character_name"]))
        target = normalize_candidate_name(str(relationship["target_character_name"]))
        summary = clean_relationship_summary(str(relationship["relation_summary"]))
        evidence = str(relationship["evidence"])
        for name in (source, target):
            if not is_reasonable_candidate_name(name, ["relationship_sentence"]):
                continue
            add_evidence(
                accumulator,
                name=name,
                source_type="relationship_sentence",
                evidence=evidence,
                parsed_id=parsed_id,
                confidence=0.78,
                relationship_evidence=summary,
            )


def extract_action_subjects(
    accumulator: dict[str, CandidatePayload],
    text: str,
    parsed_id: str,
) -> None:
    counts: defaultdict[str, int] = defaultdict(int)
    for match in re.finditer(r"(?m)^([\u4e00-\u9fff]{2,5})(?:说|问|想|看见|发现|走向|回头|离开|出现)", text):
        name = normalize_candidate_name(match.group(1))
        if is_reasonable_candidate_name(name, ["action_subject"]):
            counts[name] += 1
    for name, count in counts.items():
        if count < 2:
            continue
        add_evidence(
            accumulator,
            name=name,
            source_type="repeated_subject",
            evidence=f"{name}作为行动主体出现 {count} 次",
            parsed_id=parsed_id,
            confidence=min(0.55 + count * 0.04, 0.72),
            mention_count=count,
        )


def attach_possessive_evidence(
    accumulator: dict[str, CandidatePayload],
    clean_documents: list[tuple[ParsedDocument, str]],
) -> None:
    high_names = [
        name
        for name, payload in accumulator.items()
        if set(payload.get("source_types", [])) & {
            "current_character",
            "identity_field",
            "dialogue_label",
        }
    ]
    for document, text in clean_documents:
        for name in high_names:
            pattern = rf"{re.escape(name)}的[\u4e00-\u9fff]{{1,8}}"
            for match in re.finditer(pattern, text):
                payload = accumulator.get(name)
                if not payload:
                    continue
                append_unique(payload.setdefault("evidence_spans", []), build_evidence(text, match.start(), match.end()))
                payload["mention_count"] = int(payload.get("mention_count") or 0) + 1
                append_unique(payload.setdefault("source_document_ids", []), document.parsed_id)


def add_evidence(
    accumulator: dict[str, CandidatePayload],
    *,
    name: str,
    source_type: str,
    evidence: str,
    parsed_id: str,
    confidence: float,
    dialogue_count: int = 0,
    mention_count: int = 1,
    relationship_evidence: str = "",
) -> None:
    canonical_name = normalize_candidate_name(name)
    payload = accumulator.setdefault(
        canonical_name,
        {
            "name": canonical_name,
            "canonical_name": canonical_name,
            "display_name": canonical_name,
            "normalized_name": canonical_name,
            "aliases": [],
            "source_types": [],
            "evidence_spans": [],
            "dialogue_count": 0,
            "mention_count": 0,
            "relationship_evidence": [],
            "relationship_hints": [],
            "source_document_ids": [],
            "confidence": 0.0,
        },
    )
    append_unique(payload["source_types"], source_type)
    append_unique(payload["evidence_spans"], evidence)
    append_unique(payload["source_document_ids"], parsed_id)
    payload["dialogue_count"] = int(payload.get("dialogue_count") or 0) + dialogue_count
    payload["mention_count"] = int(payload.get("mention_count") or 0) + mention_count
    payload["confidence"] = max(float(payload.get("confidence") or 0), confidence)
    if relationship_evidence:
        append_unique(payload["relationship_evidence"], relationship_evidence)
        append_unique(payload["relationship_hints"], relationship_evidence)


def finalize_candidates(project_id: str, payloads: list[CandidatePayload]) -> list[CandidatePayload]:
    results: list[CandidatePayload] = []
    for payload in payloads:
        source_types = [str(item) for item in payload.get("source_types", [])]
        candidate_type = classify_candidate_name(str(payload["canonical_name"]), source_types)
        validation = validate_person_candidate(payload)
        if validation["candidate_type"] != "unknown":
            candidate_type = str(validation["candidate_type"])
        confidence = compute_confidence(payload, candidate_type)
        confidence_level = confidence_to_level(confidence, candidate_type, source_types)
        if validation["confidence_level"] == "low" and candidate_type != "person":
            confidence_level = "low"
        elif validation["confidence_level"] == "medium" and confidence_level == "high":
            confidence_level = "medium"
        evidence_spans = [str(item) for item in payload.get("evidence_spans", [])]
        relationship_evidence = [str(item) for item in payload.get("relationship_evidence", [])]
        payload.update(
            {
                "project_id": project_id,
                "candidate_type": candidate_type,
                "confidence": confidence,
                "confidence_level": confidence_level,
                "needs_human_review": confidence_level != "high" or candidate_type != "person",
                "identity_hint": build_identity_hint(str(payload["canonical_name"]), source_types, candidate_type),
                "personality_hint": build_personality_hint(relationship_evidence),
                "relationship_hints": relationship_evidence[:5],
                "evidence": "；".join(evidence_spans[:5])[:500],
                "rejected_reason": "",
                "merge_suggestions": [],
                "reviewer_provider": "pending",
                "reviewer_status": "pending",
                "reviewer_reason": "",
            }
        )
        results.append(payload)
    return results


def compute_confidence(payload: CandidatePayload, candidate_type: str) -> float:
    if candidate_type != "person":
        return min(float(payload.get("confidence") or 0), 0.35)
    source_types = set(payload.get("source_types", []))
    score = 0.2
    if "current_character" in source_types:
        score += 0.45
    if "identity_field" in source_types:
        score += 0.38
    if "dialogue_label" in source_types:
        score += 0.36
    if "relationship_sentence" in source_types:
        score += 0.12
    if "repeated_subject" in source_types:
        score += 0.12
    score += min(int(payload.get("dialogue_count") or 0) * 0.05, 0.15)
    score += min(int(payload.get("mention_count") or 0) * 0.02, 0.12)
    return round(min(1.0, max(score, float(payload.get("confidence") or 0))), 2)


def confidence_to_level(confidence: float, candidate_type: str, source_types: list[str]) -> str:
    if candidate_type != "person":
        return "low"
    source_set = set(source_types)
    strong_sources = {"current_character", "identity_field", "filename", "title", "llm_review"}
    dialogue_is_strong = "dialogue_label" in source_set and (
        len(source_set - {"dialogue_label", "relationship_sentence"}) > 0
        or "relationship_sentence" in source_set
    )
    if confidence >= 0.76 and (source_set & strong_sources or dialogue_is_strong):
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"


def apply_reviews(payloads: list[CandidatePayload], reviews: list[dict]) -> None:
    review_by_name = {
        str(review.get("canonical_name") or ""): review
        for review in reviews
        if review.get("canonical_name")
    }
    for payload in payloads:
        review = review_by_name.get(str(payload.get("canonical_name")))
        if not review:
            payload["reviewer_provider"] = "rule"
            payload["reviewer_status"] = "rule_fallback"
            payload["reviewer_reason"] = "Reviewer did not return this candidate; kept as low confidence for manual review."
            payload["confidence_level"] = "low"
            payload["needs_human_review"] = True
            enforce_candidate_boundaries(payload)
            continue
        payload["candidate_type"] = str(review.get("candidate_type") or payload.get("candidate_type") or "unknown")
        payload["confidence_level"] = str(review.get("confidence_level") or payload.get("confidence_level") or "low")
        payload["needs_human_review"] = bool(review.get("needs_human_review"))
        payload["reviewer_provider"] = str(review.get("reviewer_provider") or "rule")
        payload["reviewer_status"] = str(review.get("reviewer_status") or "reviewed")
        payload["reviewer_reason"] = str(review.get("reviewer_reason") or review.get("reason") or "")
        if (
            payload["reviewer_provider"] == "openai_compatible"
            and payload["candidate_type"] == "person"
            and payload["confidence_level"] == "high"
        ):
            append_unique(payload.setdefault("source_types", []), "llm_review")
        if payload["candidate_type"] != "person":
            payload["needs_human_review"] = False
        enforce_candidate_boundaries(payload)


def enforce_candidate_boundaries(payload: CandidatePayload) -> None:
    source_types = set(str(item) for item in payload.get("source_types", []))
    dialogue_count = int(payload.get("dialogue_count") or 0)
    reviewer_status = str(payload.get("reviewer_status") or "")
    validation = validate_person_candidate(payload)
    if validation["candidate_type"] in {"noise", "structure_term", "document_term", "clue", "abstract", "action_phrase", "prop", "place"}:
        payload["candidate_type"] = str(validation["candidate_type"])
        payload["confidence_level"] = "low"
        payload["needs_human_review"] = False
        return
    if payload.get("candidate_type") != "person":
        payload["confidence_level"] = "low"
        payload["needs_human_review"] = False
        return
    has_strong_source = bool(source_types & {"current_character", "identity_field", "filename", "title", "llm_review"})
    has_strong_dialogue = "dialogue_label" in source_types and (
        dialogue_count >= 2
        or bool(source_types - {"dialogue_label", "relationship_sentence"})
        or "relationship_sentence" in source_types
    )
    reviewer_high = reviewer_status == "success" and payload.get("confidence_level") == "high"
    if payload.get("confidence_level") == "high" and not (has_strong_source or has_strong_dialogue or reviewer_high):
        payload["confidence_level"] = "medium"
        payload["needs_human_review"] = True
    if payload.get("confidence_level") != "high":
        payload["needs_human_review"] = True


def build_segments_summary(clean_documents: list[tuple[ParsedDocument, str]]) -> list[dict[str, str | int]]:
    return [
        {
            "parsed_document_id": document.parsed_id,
            "filename": document.filename,
            "length": len(text),
            "preview": text[:160],
        }
        for document, text in clean_documents
    ]


def is_reasonable_candidate_name(name: str, source_types: list[str]) -> bool:
    if not (2 <= len(name) <= 5):
        return False
    validation = validate_person_candidate({"name": name, "source_types": source_types})
    if validation["candidate_type"] in {"noise", "structure_term", "document_term", "clue", "abstract", "action_phrase"}:
        return False
    candidate_type = classify_candidate_name(name, source_types)
    return candidate_type not in {"noise", "structure_term", "document_term", "clue", "abstract", "action_phrase"}


def append_unique(values: object, value: str) -> None:
    if not isinstance(values, list):
        return
    clean_value = value.strip()
    if clean_value and clean_value not in values:
        values.append(clean_value)


def clean_relationship_summary(summary: str) -> str:
    return " ".join(summary.replace("。", "").split())[:80]


def build_identity_hint(name: str, source_types: list[str], candidate_type: str) -> str:
    if candidate_type != "person":
        return f"{name}被规则归类为 {candidate_type}，默认不作为人物生成。"
    if "current_character" in source_types:
        return f"{name}可能是当前角色本所属角色。"
    if "dialogue_label" in source_types:
        return f"{name}有明确对白标签，具备人物候选强证据。"
    if "identity_field" in source_types:
        return f"{name}来自姓名/角色字段，具备人物候选强证据。"
    if "relationship_sentence" in source_types:
        return f"{name}来自关系句证据，建议用户确认。"
    return f"{name}有弱角色证据，需人工确认。"


def build_personality_hint(relationship_hints: list[str]) -> str:
    joined = "；".join(relationship_hints)
    if "宿敌" in joined:
        return "带有冲突感和对抗关系"
    if any(word in joined for word in ("情侣", "恋人", "喜欢", "暗恋", "旧识")):
        return "带有情感牵连和故事关系"
    return "当前由证据驱动识别，性格需后续资料或用户确认"
