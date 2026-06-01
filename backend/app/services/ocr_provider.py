from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import settings


MOCK_OCR_TEXT = "当前图片 OCR 使用 mock provider。请配置真实 OCR 后重新解析。"


class OCRProvider(ABC):
    provider_name: str

    @abstractmethod
    def extract_text(self, image_path: str) -> dict[str, str | float | None]:
        raise NotImplementedError


class MockOCRProvider(OCRProvider):
    provider_name = "mock"

    def __init__(self, *, fallback_reason: str | None = None) -> None:
        self.fallback_reason = fallback_reason

    def extract_text(self, image_path: str) -> dict[str, str | float | None]:
        return {
            "text": MOCK_OCR_TEXT,
            "provider": self.provider_name,
            "status": "mock_ocr",
            "confidence": 0.0,
            "error": self.fallback_reason,
            "fallback_reason": self.fallback_reason,
        }


class PaddleOCRProvider(OCRProvider):
    provider_name = "paddleocr"

    def __init__(self, *, lang: str = "ch") -> None:
        self.lang = lang

    def extract_text(self, image_path: str) -> dict[str, str | float | None]:
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            return MockOCRProvider(
                fallback_reason=f"PaddleOCR unavailable: {exc.__class__.__name__}"
            ).extract_text(image_path)

        try:
            ocr = PaddleOCR(use_angle_cls=True, lang=self.lang)
            result = ocr.ocr(str(image_path), cls=True)
            lines, confidences = flatten_paddleocr_result(result)
            text = "\n".join(lines).strip()
            if not text:
                raise ValueError("PaddleOCR returned empty text")
            confidence = (
                round(sum(confidences) / len(confidences), 4)
                if confidences
                else 0.0
            )
            return {
                "text": text,
                "provider": self.provider_name,
                "status": "success",
                "confidence": confidence,
                "error": None,
                "fallback_reason": None,
            }
        except Exception as exc:
            return MockOCRProvider(
                fallback_reason=f"PaddleOCR failed: {exc.__class__.__name__}"
            ).extract_text(image_path)


def flatten_paddleocr_result(result: Any) -> tuple[list[str], list[float]]:
    lines: list[str] = []
    confidences: list[float] = []

    def visit(node: Any) -> None:
        if isinstance(node, tuple) and len(node) >= 2 and isinstance(node[0], str):
            lines.append(node[0])
            try:
                confidences.append(float(node[1]))
            except (TypeError, ValueError):
                pass
            return
        if isinstance(node, list):
            for item in node:
                visit(item)

    visit(result)
    return lines, confidences


def is_paddleocr_available() -> bool:
    return importlib.util.find_spec("paddleocr") is not None


def get_ocr_provider() -> OCRProvider:
    if settings.ocr_provider == "paddleocr":
        if is_paddleocr_available():
            return PaddleOCRProvider(lang=settings.ocr_lang)
        return MockOCRProvider(fallback_reason="PaddleOCR is not installed")
    return MockOCRProvider()


def get_ocr_status() -> dict[str, str | bool]:
    paddle_available = is_paddleocr_available()
    active_provider = (
        "paddleocr"
        if settings.ocr_provider == "paddleocr" and paddle_available
        else "mock"
    )
    return {
        "ocr_provider": settings.ocr_provider,
        "active_provider": active_provider,
        "paddleocr_available": paddle_available,
        "ocr_lang": settings.ocr_lang,
        "pdf_image_fallback_enabled": settings.ocr_enable_pdf_image_fallback,
    }


def extract_image_text(path: Path) -> dict[str, str | float | None]:
    return get_ocr_provider().extract_text(str(path))
