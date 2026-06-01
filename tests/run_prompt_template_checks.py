from __future__ import annotations

from pathlib import Path

from common import ROOT_DIR, TestRecorder


PROMPT_DIR = ROOT_DIR / "backend" / "app" / "prompts"
REQUIRED_PROMPTS = [
    "script_corpus_analyzer.md",
    "character_extractor.md",
    "character_merger.md",
    "relationship_extractor.md",
    "profile_builder.md",
    "spoiler_classifier.md",
    "roleplay_system_prompt.md",
]


def main() -> int:
    recorder = TestRecorder("prompt_template_checks")
    prompt_texts: dict[str, str] = {}

    for filename in REQUIRED_PROMPTS:
        path = PROMPT_DIR / filename
        exists = path.exists()
        recorder.check(f"prompt exists: {filename}", exists, str(path))
        if exists:
            prompt_texts[filename] = path.read_text(encoding="utf-8")

    for filename, text in prompt_texts.items():
        if filename == "roleplay_system_prompt.md":
            continue
        recorder.check(
            f"{filename} requires JSON output",
            "JSON" in text and ("严格" in text or "strict" in text.lower()),
            {"filename": filename},
        )
        recorder.check(
            f"{filename} avoids full script reproduction",
            "不要复述完整剧本" in text or "不要输出完整剧本" in text or "不要复述完整剧本文本" in text,
            {"filename": filename},
        )

    roleplay = prompt_texts.get("roleplay_system_prompt.md", "")
    recorder.check(
        "roleplay prompt includes spoiler protection",
        "non_spoiler" in roleplay and "heavy" in roleplay and ("剧透" in roleplay or "泄露" in roleplay),
        {"file": "roleplay_system_prompt.md"},
    )
    recorder.check(
        "roleplay prompt includes first/second person perspective",
        "第一/第二人称" in roleplay or "用户是其扮演身份" in roleplay,
        {"file": "roleplay_system_prompt.md"},
    )

    candidate = prompt_texts.get("character_extractor.md", "")
    recorder.check(
        "character extractor distinguishes non-person types",
        all(keyword in candidate for keyword in ["organization", "place", "prop", "clue", "noise"]),
        {"file": "character_extractor.md"},
    )
    recorder.check(
        "character extractor documents X的Y ownership",
        "X的Y" in candidate and "不创建" in candidate,
        {"file": "character_extractor.md"},
    )

    recorder.write_report("prompt_template_report.json")
    return 1 if recorder.failed_cases else 0


if __name__ == "__main__":
    raise SystemExit(main())
