from pydantic import BaseModel


class StorageStatusResponse(BaseModel):
    storage_provider: str
    active_provider: str
    bucket_configured: bool
    endpoint_configured: bool
    public_base_url_configured: bool
    max_upload_size_mb: int
    allowed_upload_types: list[str]


class SystemHealthResponse(BaseModel):
    status: str
    database: str
    storage: str
    llm_provider: str
    ocr_provider: str
    image_provider: str
    timestamp: str
