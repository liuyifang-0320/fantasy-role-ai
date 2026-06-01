from __future__ import annotations

from common import (
    ApiClient,
    TestRecorder,
    base_url_arg,
    create_dev_user,
    upload_and_parse_txt,
    user_headers,
)


def main() -> int:
    args = base_url_arg("Run LLM-first script understanding checks.")
    client = ApiClient(args.base_url)
    recorder = TestRecorder("llm_first_script_understanding", args.base_url)
    extra: dict[str, object] = {}

    try:
        llm_status = client.get("/api/llm/status")
        user = create_dev_user(client, "Stage18 LLM First User")
        headers = user_headers(user["user_id"])
        project = client.post(
            "/api/projects",
            headers=headers,
            json_body={
                "title": "Stage18 LLM First Project",
                "description": "LLM-first script understanding regression",
                "source_type": "upload",
            },
        )
        project_id = project["project_id"]
        uploaded, parsed = upload_and_parse_txt(
            client,
            headers=headers,
            project_id=project_id,
            filename="stage18_llm_first_sample.txt",
            text=(
                "第一幕\n"
                "阿奇：戴丽拉，你还记得我吗？\n"
                "戴丽拉：我当然记得。\n"
                "阿奇和戴丽拉是情侣。\n"
                "小雪和阿奇是宿敌。\n"
                "阿奇的声音在雨里变得很轻。\n"
                "这份资料记录了第一幕的线索和真相。\n"
                "主持人提醒玩家不要提前查看凶手信息。\n"
            ),
        )
        recorder.check("upload and parse sample", parsed.get("parse_status") == "success", parsed)

        analysis = client.post(
            f"/api/projects/{project_id}/script-intelligence/llm-analyze",
            headers=headers,
            json_body={
                "parsed_document_ids": [parsed["parsed_id"]],
                "force_rebuild": False,
                "use_llm": True,
                "spoiler_mode": "non_spoiler",
                "owner_hints": [
                    {
                        "parsed_document_id": parsed["parsed_id"],
                        "owner_character_name": "阿奇",
                        "document_scope": "character_book",
                    }
                ],
            },
        )
        summary = analysis.get("summary") or {}
        provider = summary.get("provider")
        extra["analysis_summary"] = {
            "analysis_id": analysis.get("analysis_id"),
            "status": analysis.get("status"),
            "provider": provider,
            "message": summary.get("message"),
            "characters": [
                item.get("canonical_name") for item in summary.get("characters", [])
            ],
        }
        recorder.check(
            "llm-analyze endpoint returns analysis",
            bool(analysis.get("analysis_id")) and analysis.get("status") in {"success", "fallback", "partial"},
            extra["analysis_summary"],
        )
        if not llm_status.get("api_key_configured"):
            recorder.check(
                "no API key uses rule fallback, not fake LLM success",
                provider == "rule_fallback"
                and "规则 fallback" in (summary.get("message") or ""),
                extra["analysis_summary"],
            )
        else:
            recorder.check(
                "API key optional path reports provider",
                provider in {"openai_compatible", "rule_fallback"},
                extra["analysis_summary"],
            )

        status = client.get(
            f"/api/projects/{project_id}/script-intelligence/status",
            headers=headers,
        )
        recorder.check(
            "script intelligence status endpoint",
            status.get("analysis_id") == analysis.get("analysis_id"),
            status,
        )

        result = client.get(
            f"/api/projects/{project_id}/script-intelligence/result",
            headers=headers,
        )
        recorder.check(
            "script intelligence result endpoint",
            bool(result.get("result", {}).get("characters")),
            result,
        )

        candidates = client.get(f"/api/projects/{project_id}/candidates", headers=headers)
        high_people = [
            item
            for item in candidates
            if item.get("candidate_type") == "person" and item.get("confidence_level") == "high"
        ]
        garbage_high = [
            item.get("canonical_name")
            for item in high_people
            if "的" in item.get("canonical_name", "")
            or item.get("canonical_name") in {"第一幕", "线索", "真相", "主持人", "玩家", "资料", "凶手信息"}
        ]
        recorder.check(
            "old candidate API remains compatible",
            isinstance(candidates, list) and len(candidates) >= 1,
            {"count": len(candidates)},
        )
        recorder.check(
            "no large garbage high-person candidates",
            not garbage_high and len(high_people) <= 8,
            {"high_people": [item.get("canonical_name") for item in high_people], "garbage_high": garbage_high},
        )

        confirmed_ids = [item["candidate_id"] for item in high_people[:3] if item.get("candidate_id")]
        confirm = client.post(
            f"/api/projects/{project_id}/script-intelligence/confirm",
            headers=headers,
            json_body={
                "confirmed_candidate_ids": confirmed_ids,
                "confirmed_relationship_ids": [
                    item.get("relationship_id")
                    for item in summary.get("relationships", [])[:3]
                    if item.get("relationship_id")
                ],
                "spoiler_mode": "non_spoiler",
            },
        )
        recorder.check(
            "confirm endpoint usable",
            confirm.get("project_id") == project_id,
            confirm,
        )
    except Exception as exc:
        recorder.record_exception("llm-first script understanding flow", exc)

    recorder.write_report("llm_first_script_understanding_report.json", extra)
    return 1 if recorder.failed_cases else 0


if __name__ == "__main__":
    raise SystemExit(main())
