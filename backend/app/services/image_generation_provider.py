from dataclasses import dataclass

from app.core.config import settings


@dataclass
class ImageGenerationResult:
    provider: str
    status: str
    image_url: str
    local_path: str
    error: str | None = None


class ImageGenerationProvider:
    provider_name = "base"

    def generate_image(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        style: str,
    ) -> ImageGenerationResult:
        raise NotImplementedError


class MockImageProvider(ImageGenerationProvider):
    provider_name = "mock"

    MOCK_IMAGES = {
        "q_chibi": "/static/mock/generated-q.png",
        "anime_chibi": "/static/mock/generated-q.png",
        "soft_dream": "/static/mock/aqi-q.png",
        "mystery_dark": "/static/mock/generated-q.png",
        "cute_pet": "/static/mock/aqi-q.png",
    }

    def generate_image(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        style: str,
    ) -> ImageGenerationResult:
        image_url = self.MOCK_IMAGES.get(style, "/static/mock/generated-q.png")
        filename = image_url.rsplit("/", 1)[-1]
        return ImageGenerationResult(
            provider="mock",
            status="mock",
            image_url=image_url,
            local_path=f"app/static/mock/{filename}",
            error=None,
        )


class CustomImageProvider(ImageGenerationProvider):
    provider_name = "custom"

    def __init__(self) -> None:
        self.api_key = settings.image_api_key
        self.base_url = settings.image_base_url
        self.model = settings.image_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def generate_image(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        style: str,
    ) -> ImageGenerationResult:
        if not self.is_configured:
            return MockImageProvider().generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                style=style,
            )

        # Stage 12 only reserves the custom provider contract. Concrete vendor
        # protocols will be wired here later after IMAGE_PROVIDER is configured.
        mock_result = MockImageProvider().generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            style=style,
        )
        mock_result.error = "custom image provider protocol is not implemented yet"
        return mock_result


def get_image_generation_provider() -> ImageGenerationProvider:
    if settings.image_provider == "custom":
        provider = CustomImageProvider()
        if provider.is_configured:
            return provider
    return MockImageProvider()


def get_image_generation_status() -> dict:
    configured_provider = settings.image_provider
    active_provider = "mock"
    if configured_provider == "custom":
        custom_provider = CustomImageProvider()
        active_provider = "custom" if custom_provider.is_configured else "mock"

    return {
        "image_provider": configured_provider,
        "active_provider": active_provider,
        "api_key_configured": bool(settings.image_api_key),
        "base_url_configured": bool(settings.image_base_url),
        "model": settings.image_model,
        "timeout_seconds": settings.image_timeout_seconds,
    }
