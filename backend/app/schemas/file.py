from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    file_id: str
    user_id: str | None = None
    project_id: str | None = None
    filename: str
    file_type: str
    file_path: str
    storage_provider: str = "local"
    storage_key: str = ""
    public_url: str = ""
    content_type: str = ""
    file_size: int = 0
    upload_status: str


class ParsedDocumentSummary(BaseModel):
    parsed_id: str
    file_id: str
    user_id: str | None = None
    project_id: str | None = None
    filename: str
    file_type: str
    parse_status: str
    text_preview: str
    word_count: int
    ocr_provider: str = ""
    ocr_confidence: float = 0.0
    ocr_error: str | None = None
    safety_warning: str = ""
    safety_categories: list[str] = []


class ParsedDocumentDetail(ParsedDocumentSummary):
    raw_text: str
