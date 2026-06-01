import re
from abc import ABC, abstractmethod

from app.core.config import settings


class LLMProvider(ABC):
    provider_name: str

    def __init__(
        self,
        *,
        configured_provider: str,
        model: str,
        fallback: bool = False,
        fallback_reason: str | None = None,
    ) -> None:
        self.configured_provider = configured_provider
        self.model = model or "mock-model"
        self.fallback = fallback
        self.fallback_reason = fallback_reason

    @abstractmethod
    def generate_reply(self, prompt_bundle: dict[str, str | int | bool]) -> dict[str, str | bool | None]:
        raise NotImplementedError

    def build_result(
        self,
        *,
        reply: str,
        pet_action: str,
        memory_hint: str,
    ) -> dict[str, str | bool | None]:
        return {
            "reply": reply,
            "pet_action": pet_action,
            "memory_hint": memory_hint,
            "provider": self.provider_name,
            "model": self.model,
            "fallback": self.fallback,
            "fallback_reason": self.fallback_reason,
        }


class MockLLMProvider(LLMProvider):
    provider_name = "mock"

    def __init__(
        self,
        *,
        configured_provider: str = "mock",
        model: str = "mock-model",
        fallback: bool = False,
        fallback_reason: str | None = None,
    ) -> None:
        super().__init__(
            configured_provider=configured_provider,
            model=model or "mock-model",
            fallback=fallback,
            fallback_reason=fallback_reason,
        )

    def generate_reply(self, prompt_bundle: dict[str, str | int | bool]) -> dict[str, str | bool | None]:
        message = str(prompt_bundle["user_prompt"]).strip()
        character_name = str(prompt_bundle["character_name"])
        persona_name = str(
            prompt_bundle.get("nickname_for_user")
            or prompt_bundle["user_persona_name"]
        )
        relationship_label = resolve_relationship_label(prompt_bundle)
        tone_style = str(prompt_bundle.get("tone_style", "original"))
        reply_length = str(prompt_bundle.get("reply_length", "medium"))
        spoiler_protection = bool(prompt_bundle.get("spoiler_protection", True))
        pet_action, memory_hint = build_local_interaction_metadata(
            message,
            relationship_label,
        )
        is_secret_query = any(keyword in message for keyword in ("秘密", "真相", "凶手"))

        if pet_action == "shy":
            reply = f"{persona_name}，{character_name}当然记得你。你是我一直放不下的人。"
        elif pet_action == "thinking" and spoiler_protection:
            reply = f"{persona_name}，有些真相现在还不能说，但{character_name}不会丢下你。"
        elif pet_action == "comfort":
            reply = f"{persona_name}，先别一个人撑着。{character_name}会陪着你。"
        elif is_secret_query:
            reply = f"{persona_name}，我听见你在追问真相了。现在我只能把能说的部分告诉你，剩下的要等剧情走到那里。"
        else:
            reply = f"{persona_name}，{character_name}在听。只要你愿意说，我会认真回应你。"
        reply = apply_mock_style(
            reply,
            tone_style=tone_style,
            reply_length=reply_length,
            persona_name=persona_name,
            character_name=character_name,
            pet_action=pet_action,
        )

        return self.build_result(
            reply=reply,
            pet_action=pet_action,
            memory_hint=memory_hint,
        )


class OpenAICompatibleProvider(LLMProvider):
    provider_name = "openai_compatible"

    def generate_reply(self, prompt_bundle: dict[str, str | int | bool]) -> dict[str, str | bool | None]:
        from openai import OpenAI

        client_kwargs: dict[str, object] = {
            "api_key": settings.llm_api_key,
            "timeout": settings.llm_timeout_seconds,
        }
        if settings.llm_base_url:
            client_kwargs["base_url"] = settings.llm_base_url
        client = OpenAI(**client_kwargs)

        if settings.llm_api_style == "responses":
            response = client.responses.create(
                model=settings.llm_model,
                instructions=str(prompt_bundle["system_prompt"]),
                input=build_responses_input(prompt_bundle),
            )
            reply = (getattr(response, "output_text", "") or "").strip()
        else:
            completion = client.chat.completions.create(
                model=settings.llm_model,
                messages=build_chat_messages(prompt_bundle),
            )
            reply = (completion.choices[0].message.content or "").strip()

        if not reply:
            raise ValueError("Model returned an empty reply")

        pet_action, memory_hint = build_local_interaction_metadata(
            str(prompt_bundle["user_prompt"]),
            resolve_relationship_label(prompt_bundle),
        )
        return self.build_result(
            reply=reply,
            pet_action=pet_action,
            memory_hint=memory_hint,
        )


class CustomHTTPProvider(LLMProvider):
    provider_name = "custom_http"

    def generate_reply(self, prompt_bundle: dict[str, str | int | bool]) -> dict[str, str | bool | None]:
        raise NotImplementedError(
            "custom_http provider is reserved for vendor-specific adapters"
        )


def get_llm_provider() -> LLMProvider:
    configured_provider = settings.llm_provider

    if configured_provider == "mock":
        return MockLLMProvider(
            configured_provider=configured_provider,
            model="mock-model",
        )

    if configured_provider == "openai_compatible":
        missing = missing_openai_compatible_config()
        if missing:
            return build_mock_fallback(
                configured_provider=configured_provider,
                reason=f"Missing required config: {', '.join(missing)}",
            )
        return OpenAICompatibleProvider(
            configured_provider=configured_provider,
            model=settings.llm_model,
        )

    if configured_provider == "custom_http":
        missing = missing_custom_http_config()
        if missing:
            return build_mock_fallback(
                configured_provider=configured_provider,
                reason=f"Missing required config: {', '.join(missing)}",
            )
        return CustomHTTPProvider(
            configured_provider=configured_provider,
            model=settings.llm_model,
        )

    return build_mock_fallback(
        configured_provider=configured_provider,
        reason="Unsupported LLM_PROVIDER",
    )


def get_llm_status() -> dict[str, str | bool]:
    provider = get_llm_provider()
    return {
        "configured_provider": settings.llm_provider,
        "active_provider": provider.provider_name,
        "api_key_configured": bool(settings.llm_api_key),
        "base_url_configured": bool(settings.llm_base_url),
        "model": settings.llm_model or "mock-model",
        "api_style": settings.llm_api_style,
        "prompt_debug_enabled": settings.enable_prompt_debug,
    }


def build_mock_fallback(*, configured_provider: str, reason: str) -> MockLLMProvider:
    return MockLLMProvider(
        configured_provider=configured_provider,
        model="mock-model",
        fallback=True,
        fallback_reason=reason,
    )


def missing_openai_compatible_config() -> list[str]:
    missing: list[str] = []
    if not settings.llm_api_key:
        missing.append("LLM_API_KEY")
    if not settings.llm_model or settings.llm_model == "mock-model":
        missing.append("LLM_MODEL")
    return missing


def missing_custom_http_config() -> list[str]:
    missing: list[str] = []
    if not settings.llm_api_key:
        missing.append("LLM_API_KEY")
    if not settings.llm_base_url:
        missing.append("LLM_BASE_URL")
    if not settings.llm_model or settings.llm_model == "mock-model":
        missing.append("LLM_MODEL")
    return missing


def build_chat_messages(prompt_bundle: dict[str, str | int | bool]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": str(prompt_bundle["system_prompt"])},
        {"role": "user", "content": str(prompt_bundle["settings_prompt"])},
        {"role": "user", "content": str(prompt_bundle["memory_prompt"])},
        {"role": "user", "content": str(prompt_bundle["knowledge_prompt"])},
        {"role": "user", "content": str(prompt_bundle["context_prompt"])},
        {"role": "user", "content": str(prompt_bundle["user_prompt"])},
    ]


def build_responses_input(prompt_bundle: dict[str, str | int | bool]) -> str:
    return "\n\n".join(
        [
            str(prompt_bundle["settings_prompt"]),
            str(prompt_bundle["memory_prompt"]),
            str(prompt_bundle["knowledge_prompt"]),
            str(prompt_bundle["context_prompt"]),
            str(prompt_bundle["user_prompt"]),
        ]
    ).strip()


def apply_mock_style(
    reply: str,
    *,
    tone_style: str,
    reply_length: str,
    persona_name: str,
    character_name: str,
    pet_action: str,
) -> str:
    if reply_length == "short":
        short_replies = {
            "comfort": f"{persona_name}，别硬撑，我在。",
            "thinking": f"{persona_name}，真相现在还不能说。",
            "shy": f"{persona_name}，我当然记得你。",
        }
        return short_replies.get(pet_action, f"{persona_name}，我在听。")

    if pet_action == "thinking":
        if reply_length == "long":
            return (
                f"{reply} 我会陪你走到答案出现的地方，"
                "但不会越过剧本现在允许说出的边界。"
            )
        return reply

    if tone_style == "cold":
        reply = f"{persona_name}，我听见了。{character_name}不会说多余的话，但会把该守住的事守住。"
    elif tone_style == "playful":
        reply = f"{persona_name}，你一开口我就听见啦。{character_name}会认真陪你，不过别想从我这里轻易套走秘密。"
    elif tone_style == "mature":
        reply = f"{persona_name}，慢慢说，我会稳稳接住你。{character_name}会替你把情绪和分寸都照看好。"
    elif tone_style == "yandere_light":
        reply = f"{persona_name}，我当然会在意你。{character_name}只是希望你别把这些话说给别人听。"
    elif tone_style == "poetic":
        reply = f"{persona_name}，你的声音像旧街区的雨。{character_name}会把能说的话轻轻放到你手心。"
    elif tone_style == "gentle":
        reply = f"{persona_name}，别急。{character_name}会温柔一点陪你，把话慢慢说清楚。"

    if reply_length == "long":
        reply = (
            f"{reply} 你不用急着把所有事都说明白。"
            "如果资料里还没有答案，我不会替剧本编造真相；如果那是秘密，我会把悬念留在该留的位置。"
        )
    return reply


def resolve_relationship_label(prompt_bundle: dict[str, str | int | bool]) -> str:
    label = str(prompt_bundle.get("relationship_label", "")).strip()
    if 0 < len(label) <= 12:
        return label

    relationship = str(prompt_bundle.get("relationship", "")).strip()
    match = re.search(r"[“\"]([^”\"]{1,12})[”\"]", relationship)
    if match:
        return match.group(1)
    return relationship[:12] or "重要关系"


def build_local_interaction_metadata(
    message: str,
    relationship_label: str,
) -> tuple[str, str]:
    normalized_message = message.strip()
    if any(keyword in normalized_message for keyword in ("秘密", "真相", "凶手")):
        return "thinking", "角色触发了防剧透回应，保留关键真相。"
    if any(keyword in normalized_message for keyword in ("记得我吗", "还记得我吗")):
        return "shy", "角色主动确认了与你的关系记忆。"
    if any(keyword in normalized_message for keyword in ("难过", "累", "想哭", "不开心")):
        return "comfort", "角色识别到你的低落情绪并进行安抚。"
    return "talking", f"角色维持着与你“{relationship_label}”的关系设定。"
