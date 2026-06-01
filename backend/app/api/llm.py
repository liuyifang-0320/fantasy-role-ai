from fastapi import APIRouter

from app.schemas.llm import LLMStatusResponse
from app.services.llm_provider import get_llm_status


router = APIRouter()


@router.get("/status", response_model=LLMStatusResponse)
def get_status() -> LLMStatusResponse:
    return LLMStatusResponse(**get_llm_status())
