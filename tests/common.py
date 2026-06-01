from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = Path(__file__).resolve().parent / "reports"
TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


class ApiError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, body: Any):
        super().__init__(f"{method} {path} failed with {status}: {body}")
        self.method = method
        self.path = path
        self.status = status
        self.body = body


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: Any | None = None,
        raw_body: bytes | None = None,
        content_type: str | None = None,
        timeout: int = 30,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> tuple[int, Any]:
        url = self.base_url + path
        request_headers = dict(headers or {})
        body = raw_body
        if json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            request_headers["Content-Type"] = "application/json; charset=utf-8"
        elif content_type:
            request_headers["Content-Type"] = content_type

        req = urllib.request.Request(
            url,
            data=body,
            headers=request_headers,
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = decode_response(resp.read())
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            payload = decode_response(exc.read())

        if expected_status is not None:
            expected = (
                (expected_status,)
                if isinstance(expected_status, int)
                else tuple(expected_status)
            )
            if status not in expected:
                raise ApiError(method, path, status, payload)
        elif status >= 400:
            raise ApiError(method, path, status, payload)
        return status, payload

    def get(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> Any:
        return self.request(
            "GET", path, headers=headers, expected_status=expected_status
        )[1]

    def post(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: Any | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> Any:
        return self.request(
            "POST",
            path,
            headers=headers,
            json_body=json_body,
            expected_status=expected_status,
        )[1]

    def patch(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: Any | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> Any:
        return self.request(
            "PATCH",
            path,
            headers=headers,
            json_body=json_body,
            expected_status=expected_status,
        )[1]

    def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> Any:
        return self.request(
            "DELETE", path, headers=headers, expected_status=expected_status
        )[1]

    def upload_file(
        self,
        path: str,
        *,
        headers: dict[str, str] | None,
        fields: dict[str, str] | None,
        file_field: str,
        filename: str,
        content: bytes,
        content_type: str = "text/plain",
    ) -> Any:
        boundary = "----fantasy-role-ai-test-" + uuid.uuid4().hex
        chunks: list[bytes] = []
        for key, value in (fields or {}).items():
            chunks.append(f"--{boundary}\r\n".encode("ascii"))
            chunks.append(
                (
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                    f"{value}\r\n"
                ).encode("utf-8")
            )
        chunks.append(f"--{boundary}\r\n".encode("ascii"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(content)
        chunks.append(b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode("ascii"))
        return self.request(
            "POST",
            path,
            headers=headers,
            raw_body=b"".join(chunks),
            content_type=f"multipart/form-data; boundary={boundary}",
        )[1]


@dataclass
class TestRecorder:
    name: str
    base_url: str = ""
    cases: list[dict[str, Any]] = field(default_factory=list)
    failed_cases: list[dict[str, Any]] = field(default_factory=list)

    def check(self, case_name: str, condition: bool, detail: Any = None) -> bool:
        status = "PASS" if condition else "FAIL"
        print(f"[{status}] {case_name}")
        if detail is not None:
            print(f"       {json.dumps(detail, ensure_ascii=False)}")
        item = {"name": case_name, "status": status, "detail": detail}
        self.cases.append(item)
        if not condition:
            self.failed_cases.append(item)
        return condition

    def record_exception(self, case_name: str, exc: BaseException) -> None:
        self.check(
            case_name,
            False,
            {"error": type(exc).__name__, "message": str(exc)},
        )

    def write_report(self, filename: str, extra: dict[str, Any] | None = None) -> Path:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "name": self.name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "base_url": self.base_url,
            "total": len(self.cases),
            "passed": sum(1 for case in self.cases if case["status"] == "PASS"),
            "failed": len(self.failed_cases),
            "failed_cases": self.failed_cases,
            "cases": self.cases,
        }
        if extra:
            report.update(extra)
        path = REPORT_DIR / filename
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReport written: {path}")
        return path


def decode_response(raw: bytes) -> Any:
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def base_url_arg(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL, default http://127.0.0.1:8000",
    )
    return parser.parse_args()


def user_headers(user_id: str) -> dict[str, str]:
    return {"X-User-Id": user_id}


def load_test_data(name: str) -> str:
    return (TEST_DATA_DIR / name).read_text(encoding="utf-8")


def create_dev_user(client: ApiClient, nickname: str) -> dict[str, Any]:
    return client.post("/api/auth/dev-login", json_body={"nickname": nickname})


def upload_and_parse_txt(
    client: ApiClient,
    *,
    headers: dict[str, str],
    project_id: str,
    filename: str,
    text: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    uploaded = client.upload_file(
        "/api/files/upload",
        headers=headers,
        fields={"project_id": project_id},
        file_field="file",
        filename=filename,
        content=text.encode("utf-8"),
        content_type="text/plain",
    )
    parsed = client.post(f"/api/files/{uploaded['file_id']}/parse", headers=headers)
    return uploaded, parsed


def generate_character(
    client: ApiClient,
    *,
    headers: dict[str, str],
    project_id: str,
    file_id: str,
    target_character_name: str,
    user_persona_name: str,
    relationship_hint: str,
) -> dict[str, Any]:
    return client.post(
        "/api/characters/generate",
        headers=headers,
        json_body={
            "project_id": project_id,
            "uploaded_file_ids": [file_id],
            "target_character_name": target_character_name,
            "user_persona_name": user_persona_name,
            "relationship_hint": relationship_hint,
        },
    )
