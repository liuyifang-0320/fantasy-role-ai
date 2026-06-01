import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared in requirements.txt
    def load_dotenv(*args, **kwargs):
        return False


class Settings:
    def __init__(self) -> None:
        self.app_name = "Fantasy Role AI"
        self.backend_dir = Path(__file__).resolve().parents[2]
        self.project_dir = self.backend_dir.parent
        load_dotenv(self.project_dir / ".env", override=False)

        self.app_dir = self.backend_dir / "app"
        self.upload_dir = self.app_dir / "uploads"
        self.static_dir = self.app_dir / "static"
        self.database_path = self.backend_dir / "fantasy_role_ai.db"
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./fantasy_role_ai.db")
        self.database_echo = parse_bool(
            os.getenv("DATABASE_ECHO", "false"),
            default=False,
        )
        self.allowed_upload_types = parse_csv(
            os.getenv("ALLOWED_UPLOAD_TYPES", "pdf,docx,txt,png,jpg,jpeg"),
            default=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        )
        self.allowed_upload_extensions = {
            f".{file_type.lower().lstrip('.')}"
            for file_type in self.allowed_upload_types
            if file_type.strip()
        }
        self.max_upload_size_mb = parse_int(
            os.getenv("MAX_UPLOAD_SIZE_MB", "50"),
            default=50,
        )
        self.max_upload_size_bytes = self.max_upload_size_mb * 1024 * 1024
        self.storage_provider = normalize_choice(
            os.getenv("STORAGE_PROVIDER", "local"),
            allowed={"local", "s3_compatible", "custom"},
            default="local",
        )
        self.storage_endpoint_url = os.getenv("STORAGE_ENDPOINT_URL", "")
        self.storage_bucket = os.getenv("STORAGE_BUCKET", "")
        self.storage_access_key_id = os.getenv("STORAGE_ACCESS_KEY_ID", "")
        self.storage_secret_access_key = os.getenv("STORAGE_SECRET_ACCESS_KEY", "")
        self.storage_region = os.getenv("STORAGE_REGION", "")
        self.storage_public_base_url = os.getenv("STORAGE_PUBLIC_BASE_URL", "")
        self.cors_allow_origins = parse_csv(
            os.getenv(
                "CORS_ALLOW_ORIGINS",
                "http://127.0.0.1:5173,http://localhost:5173",
            ),
            default=["http://127.0.0.1:5173", "http://localhost:5173"],
        )
        self.pet_actions = [
            "idle",
            "happy",
            "shy",
            "thinking",
            "talking",
            "comfort",
            "surprised",
        ]

        self.llm_provider = normalize_choice(
            os.getenv("LLM_PROVIDER", "mock"),
            allowed={"mock", "openai_compatible", "custom_http"},
            default="mock",
        )
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "")
        self.llm_model = os.getenv("LLM_MODEL", "mock-model")
        self.llm_api_style = normalize_choice(
            os.getenv("LLM_API_STYLE", "chat_completions"),
            allowed={"chat_completions", "responses"},
            default="chat_completions",
        )
        self.enable_prompt_debug = parse_bool(
            os.getenv("ENABLE_PROMPT_DEBUG", "true"),
            default=True,
        )
        self.enable_debug_output = parse_bool(
            os.getenv("ENABLE_DEBUG_OUTPUT", "true"),
            default=True,
        )
        self.llm_timeout_seconds = parse_int(
            os.getenv("LLM_TIMEOUT_SECONDS", "30"),
            default=30,
        )
        self.ocr_provider = normalize_choice(
            os.getenv("OCR_PROVIDER", "mock"),
            allowed={"mock", "paddleocr"},
            default="mock",
        )
        self.ocr_lang = os.getenv("OCR_LANG", "ch").strip() or "ch"
        self.ocr_enable_pdf_image_fallback = parse_bool(
            os.getenv("OCR_ENABLE_PDF_IMAGE_FALLBACK", "false"),
            default=False,
        )
        self.image_provider = normalize_choice(
            os.getenv("IMAGE_PROVIDER", "mock"),
            allowed={"mock", "custom"},
            default="mock",
        )
        self.image_api_key = os.getenv("IMAGE_API_KEY", "")
        self.image_base_url = os.getenv("IMAGE_BASE_URL", "")
        self.image_model = os.getenv("IMAGE_MODEL", "mock-image-model")
        self.image_timeout_seconds = parse_int(
            os.getenv("IMAGE_TIMEOUT_SECONDS", "60"),
            default=60,
        )
        self.safety_mode = normalize_choice(
            os.getenv("SAFETY_MODE", "rule"),
            allowed={"off", "rule", "mock_provider"},
            default="rule",
        )
        self.safety_strict_level = normalize_choice(
            os.getenv("SAFETY_STRICT_LEVEL", "normal"),
            allowed={"low", "normal", "strict"},
            default="normal",
        )
        self.enable_user_data_delete = parse_bool(
            os.getenv("ENABLE_USER_DATA_DELETE", "true"),
            default=True,
        )
        self.enable_user_data_export = parse_bool(
            os.getenv("ENABLE_USER_DATA_EXPORT", "true"),
            default=True,
        )
        self.privacy_contact_email = os.getenv("PRIVACY_CONTACT_EMAIL", "").strip()


def normalize_choice(value: str, *, allowed: set[str], default: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in allowed else default


def parse_bool(value: str, *, default: bool) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def parse_int(value: str, *, default: int) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def parse_csv(value: str, *, default: list[str]) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or default


settings = Settings()
