from __future__ import annotations

from common import (
    ApiClient,
    TestRecorder,
    base_url_arg,
    create_dev_user,
    generate_character,
    load_test_data,
    upload_and_parse_txt,
    user_headers,
)


def main() -> int:
    args = base_url_arg("Run project-level knowledge isolation checks.")
    client = ApiClient(args.base_url)
    recorder = TestRecorder("project_isolation", args.base_url)
    project_a_retrieval: dict[str, object] = {}
    project_b_retrieval: dict[str, object] = {}

    try:
        user = create_dev_user(client, "Stage17 Project Isolation User")
        headers = user_headers(user["user_id"])
        project_a = client.post(
            "/api/projects",
            headers=headers,
            json_body={
                "title": "Stage17 Isolation A",
                "description": "阿奇和戴丽拉是情侣",
                "source_type": "upload",
            },
        )
        project_b = client.post(
            "/api/projects",
            headers=headers,
            json_body={
                "title": "Stage17 Isolation B",
                "description": "阿奇和小雪是宿敌",
                "source_type": "upload",
            },
        )
        recorder.check("Create project A/B", project_a["project_id"] != project_b["project_id"], {
            "project_A": project_a["project_id"],
            "project_B": project_b["project_id"],
        })

        upload_a, _ = upload_and_parse_txt(
            client,
            headers=headers,
            project_id=project_a["project_id"],
            filename="stage17_isolation_a.txt",
            text=(
                "第一幕\n"
                "阿奇：戴丽拉，你还记得我吗？\n"
                "戴丽拉：我当然记得。\n"
                "阿奇和戴丽拉是情侣。\n"
                "戴丽拉喜欢阿奇。\n"
            ),
        )
        upload_b, _ = upload_and_parse_txt(
            client,
            headers=headers,
            project_id=project_b["project_id"],
            filename="stage17_isolation_b.txt",
            text=(
                "第一幕\n"
                "阿奇：小雪，你为什么又出现了？\n"
                "小雪：因为我一直没忘记你。\n"
                "阿奇和小雪是宿敌。\n"
                "小雪知道一条隐藏线索。\n"
            ),
        )
        recorder.check("Upload and parse project A/B files", bool(upload_a["file_id"] and upload_b["file_id"]))

        char_a = generate_character(
            client,
            headers=headers,
            project_id=project_a["project_id"],
            file_id=upload_a["file_id"],
            target_character_name="阿奇",
            user_persona_name="戴丽拉",
            relationship_hint="情侣",
        )
        char_b = generate_character(
            client,
            headers=headers,
            project_id=project_b["project_id"],
            file_id=upload_b["file_id"],
            target_character_name="阿奇",
            user_persona_name="小雪",
            relationship_hint="宿敌",
        )
        recorder.check("Generate same-name characters in project A/B", char_a["character_id"] != char_b["character_id"], {
            "char_A": char_a["character_id"],
            "char_B": char_b["character_id"],
        })

        chat_a = client.post(
            "/api/chat",
            headers=headers,
            json_body={
                "character_id": char_a["character_id"],
                "message": "阿奇和戴丽拉是什么关系？",
            },
        )
        debug_a = chat_a.get("prompt_debug") or {}
        previews_a = debug_a.get("retrieved_chunks_preview") or []
        combined_a = " ".join(item.get("content_preview", "") for item in previews_a)
        expected_a = ["戴丽拉", "情侣"]
        forbidden_a = ["小雪", "宿敌"]
        project_a_retrieval = {
            "retrieval_project_scope": debug_a.get("retrieval_project_scope"),
            "retrieved_chunk_count": debug_a.get("retrieved_chunk_count", 0),
            "retrieved_chunks_preview": previews_a,
            "combined_preview": combined_a,
            "expected_keywords": expected_a,
            "forbidden_keywords": forbidden_a,
        }
        recorder.check(
            "Project A retrieval_project_scope=project_bound",
            debug_a.get("retrieval_project_scope") == "project_bound",
            project_a_retrieval,
        )
        recorder.check(
            "Project A retrieval hits own project content",
            debug_a.get("retrieved_chunk_count", 0) >= 1
            and len(previews_a) >= 1
            and any(keyword in combined_a for keyword in expected_a),
            project_a_retrieval,
        )
        recorder.check(
            "Project A retrieval does not include project B content",
            all(keyword not in combined_a for keyword in forbidden_a),
            project_a_retrieval,
        )

        chat_b = client.post(
            "/api/chat",
            headers=headers,
            json_body={
                "character_id": char_b["character_id"],
                "message": "阿奇和小雪是什么关系？",
            },
        )
        debug_b = chat_b.get("prompt_debug") or {}
        previews_b = debug_b.get("retrieved_chunks_preview") or []
        combined_b = " ".join(item.get("content_preview", "") for item in previews_b)
        expected_b = ["小雪", "宿敌"]
        forbidden_b = ["戴丽拉", "情侣"]
        project_b_retrieval = {
            "retrieval_project_scope": debug_b.get("retrieval_project_scope"),
            "retrieved_chunk_count": debug_b.get("retrieved_chunk_count", 0),
            "retrieved_chunks_preview": previews_b,
            "combined_preview": combined_b,
            "expected_keywords": expected_b,
            "forbidden_keywords": forbidden_b,
        }
        recorder.check(
            "Project B retrieval_project_scope=project_bound",
            debug_b.get("retrieval_project_scope") == "project_bound",
            project_b_retrieval,
        )
        recorder.check(
            "Project B retrieval hits own project content",
            debug_b.get("retrieved_chunk_count", 0) >= 1
            and len(previews_b) >= 1
            and any(keyword in combined_b for keyword in expected_b),
            project_b_retrieval,
        )
        recorder.check(
            "Project B retrieval does not include project A content",
            all(keyword not in combined_b for keyword in forbidden_b),
            project_b_retrieval,
        )
    except Exception as exc:
        recorder.record_exception("project isolation unexpected error", exc)

    recorder.write_report(
        "project_isolation_report.json",
        {
            "project_A_retrieval": project_a_retrieval,
            "project_B_retrieval": project_b_retrieval,
        },
    )
    return 0 if not recorder.failed_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
