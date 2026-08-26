from anthropic import Anthropic
from mistralai.client import Mistral
from openai import OpenAI

from core.config import settings

_openai_client: OpenAI | None = None
_anthropic_client: Anthropic | None = None
_mistral_client: Mistral | None = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_anthropic_client() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_mistral_client() -> Mistral:
    global _mistral_client
    if _mistral_client is None:
        _mistral_client = Mistral(api_key=settings.mistral_api_key)
    return _mistral_client


def _generate_openai(system_prompt: str, user_prompt: str) -> str:
    response = _get_openai_client().chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _generate_anthropic(system_prompt: str, user_prompt: str) -> str:
    response = _get_anthropic_client().messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        temperature=0.1,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text if response.content else ""


def _generate_mistral(system_prompt: str, user_prompt: str) -> str:
    response = _get_mistral_client().chat.complete(
        model="mistral-small-latest",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


_PROVIDERS = {
    "openai": _generate_openai,
    "anthropic": _generate_anthropic,
    "mistral": _generate_mistral,
}


def generate_answer(system_prompt: str, user_prompt: str) -> str:
    provider = settings.llm_provider.lower()
    generate_fn = _PROVIDERS.get(provider)
    if generate_fn is None:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Must be one of {sorted(_PROVIDERS)}.")
    return generate_fn(system_prompt, user_prompt)
