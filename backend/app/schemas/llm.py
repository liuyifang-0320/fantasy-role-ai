from pydantic import BaseModel


class LLMStatusResponse(BaseModel):
    configured_provider: str
    active_provider: str
    api_key_configured: bool
    base_url_configured: bool
    model: str
    api_style: str
    prompt_debug_enabled: bool
