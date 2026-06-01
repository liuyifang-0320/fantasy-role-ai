from pydantic import BaseModel


class OCRStatusResponse(BaseModel):
    ocr_provider: str
    active_provider: str
    paddleocr_available: bool
    ocr_lang: str
    pdf_image_fallback_enabled: bool
