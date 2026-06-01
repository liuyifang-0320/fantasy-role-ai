import json


def canonicalize_name(name: str) -> str:
    return "".join((name or "").split()).strip("：:【】《》「」“”\"' ")


def normalize_name(name: str) -> str:
    return canonicalize_name(name)


def merge_candidate_payloads(payloads: list[dict]) -> list[dict]:
    by_name: dict[str, dict] = {}
    for payload in payloads:
        canonical_name = canonicalize_name(str(payload.get("canonical_name") or payload.get("name") or ""))
        if not canonical_name:
            continue
        payload["canonical_name"] = canonical_name
        payload["normalized_name"] = normalize_name(canonical_name)
        existing = by_name.get(canonical_name)
        if not existing:
            by_name[canonical_name] = payload
            continue
        existing["source_types"] = merge_lists(existing.get("source_types", []), payload.get("source_types", []))
        existing["evidence_spans"] = merge_lists(existing.get("evidence_spans", []), payload.get("evidence_spans", []), limit=12)
        existing["relationship_evidence"] = merge_lists(existing.get("relationship_evidence", []), payload.get("relationship_evidence", []), limit=8)
        existing["relationship_hints"] = merge_lists(existing.get("relationship_hints", []), payload.get("relationship_hints", []), limit=8)
        existing["source_document_ids"] = merge_lists(existing.get("source_document_ids", []), payload.get("source_document_ids", []))
        existing["dialogue_count"] = int(existing.get("dialogue_count") or 0) + int(payload.get("dialogue_count") or 0)
        existing["mention_count"] = int(existing.get("mention_count") or 0) + int(payload.get("mention_count") or 0)
        existing["confidence"] = max(float(existing.get("confidence") or 0), float(payload.get("confidence") or 0))
        if len(str(payload.get("evidence") or "")) > len(str(existing.get("evidence") or "")):
            existing["evidence"] = payload.get("evidence")
    return list(by_name.values())


def merge_lists(existing: object, incoming: object, *, limit: int = 20) -> list[str]:
    values: list[str] = []
    for value in [*as_list(existing), *as_list(incoming)]:
        text = str(value).strip()
        if text and text not in values:
            values.append(text)
        if len(values) >= limit:
            break
    return values


def as_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
        return parsed if isinstance(parsed, list) else []
    return [value]
