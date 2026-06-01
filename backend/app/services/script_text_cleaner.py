import re


MOJIBAKE_PATTERN = re.compile(r"[锟�]{2,}|(?:[ÃÂ][\x80-\xff]?){2,}")
PAGE_PATTERN = re.compile(r"^(?:第?\s*\d+\s*页|page\s*\d+|\d+\s*/\s*\d+)$", re.IGNORECASE)
DECORATION_PATTERN = re.compile(r"^[A-Z\s_\-=*]{8,}$")


def clean_script_text(raw_text: str, filename: str = "") -> dict[str, object]:
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    noise_samples: list[str] = []
    cleaned_lines: list[str] = []
    previous_line = ""

    for raw_line in text.split("\n"):
        line = normalize_line(raw_line)
        if not line:
            if cleaned_lines and cleaned_lines[-1]:
                cleaned_lines.append("")
            continue
        reason = classify_noise_line(line)
        if reason:
            append_sample(noise_samples, f"{reason}: {line}")
            continue
        if len(line) == 1 and re.fullmatch(r"[\u4e00-\u9fffA-Za-z]", line):
            append_sample(noise_samples, f"isolated: {line}")
            continue
        if line == previous_line:
            append_sample(noise_samples, f"duplicate: {line}")
            continue
        cleaned_lines.append(line)
        previous_line = line

    clean_text = merge_wrapped_lines("\n".join(cleaned_lines))
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()
    removed_noise_count = len(noise_samples)
    warning_level = "none"
    if removed_noise_count >= 12 or len(clean_text) < len(text) * 0.45:
        warning_level = "heavy"
    elif removed_noise_count >= 4:
        warning_level = "mild"

    warnings: list[str] = []
    if warning_level != "none":
        warnings.append(f"{filename or 'document'} cleaned with {warning_level} OCR/noise warning")

    return {
        "clean_text": clean_text,
        "removed_noise_count": removed_noise_count,
        "noise_samples": noise_samples[:10],
        "ocr_warning_level": warning_level,
        "warnings": warnings,
    }


def normalize_line(line: str) -> str:
    normalized = line.strip().lstrip("\ufeff")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace("： ", "：").replace(": ", ":")
    return normalized


def classify_noise_line(line: str) -> str:
    lowered = line.lower()
    if PAGE_PATTERN.fullmatch(line):
        return "page"
    if lowered in {"image", "scan", "scanned", "alt", "null", "none"}:
        return "scan-marker"
    if "watermark" in lowered or "水印" in line:
        return "watermark"
    if DECORATION_PATTERN.fullmatch(line):
        return "decoration"
    if MOJIBAKE_PATTERN.search(line):
        return "mojibake"
    if len(line) <= 3 and re.fullmatch(r"[-=_*·•\s]+", line):
        return "decoration"
    return ""


def merge_wrapped_lines(text: str) -> str:
    lines = text.split("\n")
    merged: list[str] = []
    for line in lines:
        if not line:
            merged.append("")
            continue
        if (
            merged
            and merged[-1]
            and not re.search(r"[。！？!?：:]$", merged[-1])
            and not re.match(r"^(第.+[幕章]|Chapter\s+\d+)", merged[-1], re.IGNORECASE)
            and not re.match(r"^(第.+[幕章]|Chapter\s+\d+)", line, re.IGNORECASE)
            and len(merged[-1]) < 80
            and len(line) < 80
        ):
            merged[-1] = f"{merged[-1]}{line}"
        else:
            merged.append(line)
    return "\n".join(merged)


def append_sample(samples: list[str], sample: str) -> None:
    if len(samples) < 20 and sample not in samples:
        samples.append(sample[:160])
