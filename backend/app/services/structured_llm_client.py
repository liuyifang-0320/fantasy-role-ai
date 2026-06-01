from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import LLMExtractionRun
from app.services.ids import next_prefixed_id


MAX_INPUT_PREVIEW = 1200
MAX_OUTPUT_PREVIEW = 1200
MAX_PAYLOAD_CHARS = 18000


@dataclass
class StructuredLLMResult:
    data: Any
    provider: str
    model: str
    status: str
    error: str = ""
    fallback: bool = False


FallbackFactory = Callable[[str], Any]


class StructuredLLMClient:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def generate_json(
        self,
        *,
        project_id: str,
        user_id: str | None,
        prompt_type: str,
        system_prompt: str,
        payload: dict[str, Any],
        fallback_factory: FallbackFactory,
    ) -> StructuredLLMResult:
        compact_payload = self._compact_payload(payload)
        if not self._can_call_real_llm():
            reason = "当前未配置真实 LLM API，已使用规则 fallback，结果仅供测试。"
            data = fallback_factory(reason)
            self._log_run(
                project_id=project_id,
                user_id=user_id,
                prompt_type=prompt_type,
                provider="rule_fallback",
                model=settings.llm_model or "mock-model",
                input_preview=json.dumps(compact_payload, ensure_ascii=False)[:MAX_INPUT_PREVIEW],
                output_preview=json.dumps(data, ensure_ascii=False)[:MAX_OUTPUT_PREVIEW],
                status="fallback",
                error=reason,
            )
            return StructuredLLMResult(
                data=data,
                provider="rule_fallback",
                model=settings.llm_model or "mock-model",
                status="fallback",
                error=reason,
                fallback=True,
            )

        try:
            raw_text = self._call_openai_compatible(system_prompt, compact_payload)
            data = extract_json(raw_text)
            self._log_run(
                project_id=project_id,
                user_id=user_id,
                prompt_type=prompt_type,
                provider="openai_compatible",
                model=settings.llm_model,
                input_preview=json.dumps(compact_payload, ensure_ascii=False)[:MAX_INPUT_PREVIEW],
                output_preview=raw_text[:MAX_OUTPUT_PREVIEW],
                status="success",
                error="",
            )
            return StructuredLLMResult(
                data=data,
                provider="openai_compatible",
                model=settings.llm_model,
                status="success",
            )
        except Exception as exc:
            reason = safe_error(exc)
            data = fallback_factory(f"LLM 调用或 JSON 解析失败，已回退规则结果：{reason}")
            self._log_run(
                project_id=project_id,
                user_id=user_id,
                prompt_type=prompt_type,
                provider="rule_fallback",
                model=settings.llm_model or "mock-model",
                input_preview=json.dumps(compact_payload, ensure_ascii=False)[:MAX_INPUT_PREVIEW],
                output_preview=json.dumps(data, ensure_ascii=False)[:MAX_OUTPUT_PREVIEW],
                status="fallback",
                error=reason,
            )
            return StructuredLLMResult(
                data=data,
                provider="rule_fallback",
                model=settings.llm_model or "mock-model",
                status="fallback",
                error=reason,
                fallback=True,
            )

    def _can_call_real_llm(self) -> bool:
        return (
            settings.llm_provider == "openai_compatible"
            and bool(settings.llm_api_key)
            and bool(settings.llm_model)
            and settings.llm_model != "mock-model"
        )

    def _call_openai_compatible(self, system_prompt: str, payload: dict[str, Any]) -> str:
        from openai import OpenAI

        client_kwargs: dict[str, Any] = {
            "api_key": settings.llm_api_key,
            "timeout": settings.llm_timeout_seconds,
        }
        if settings.llm_base_url:
            client_kwargs["base_url"] = settings.llm_base_url
        client = OpenAI(**client_kwargs)
        completion = client.chat.completions.create(
            model=settings.llm_model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False),
                },
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
        if not text:
            raise ValueError("LLM returned empty content")
        return text

    def _compact_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = json.dumps(payload, ensure_ascii=False)
        if len(text) <= MAX_PAYLOAD_CHARS:
            return payload
        compact = dict(payload)
        if isinstance(compact.get("chunks"), list):
            compact["chunks"] = compact["chunks"][:40]
        if isinstance(compact.get("documents"), list):
            compact["documents"] = [
                {**document, "preview": str(document.get("preview", ""))[:300]}
                for document in compact["documents"][:30]
            ]
        compact["truncated_for_llm"] = True
        return compact

    def _log_run(
        self,
        *,
        project_id: str,
        user_id: str | None,
        prompt_type: str,
        provider: str,
        model: str,
        input_preview: str,
        output_preview: str,
        status: str,
        error: str,
    ) -> None:
        if not self.db:
            return
        run = LLMExtractionRun(
            run_id=next_prefixed_id(self.db, LLMExtractionRun, "llmrun"),
            user_id=user_id,
            project_id=project_id,
            prompt_type=prompt_type,
            provider=provider,
            model=model,
            input_preview=input_preview,
            output_preview=output_preview,
            status=status,
            error=error,
        )
        self.db.add(run)
        self.db.flush()


def extract_json(text: str) -> Any:
    clean = text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"```$", "", clean).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", clean, flags=re.S)
    if not match:
        raise ValueError("No JSON object or array found in LLM output")
    return json.loads(match.group(1))


def safe_error(exc: Exception) -> str:
    text = str(exc).replace(settings.llm_api_key or "", "[redacted]")
    return text[:300] or exc.__class__.__name__
