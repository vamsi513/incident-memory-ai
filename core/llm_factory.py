from dataclasses import dataclass

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from core.config import settings
from core.exceptions import ProviderError


@dataclass
class JudgeResult:
    score: float
    rationale: str


class BaseJudgeProvider:
    async def judge_retrieval(self, prompt: str, answer: str, context: str) -> JudgeResult:
        raise NotImplementedError


class OpenAIJudgeProvider(BaseJudgeProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def judge_retrieval(self, prompt: str, answer: str, context: str) -> JudgeResult:
        _ = (prompt, answer, context)
        return JudgeResult(score=0.0, rationale="Judge provider scaffold.")


class AnthropicJudgeProvider(BaseJudgeProvider):
    def __init__(self) -> None:
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def judge_retrieval(self, prompt: str, answer: str, context: str) -> JudgeResult:
        _ = (prompt, answer, context)
        return JudgeResult(score=0.0, rationale="Judge provider scaffold.")


class LLMProviderFactory:
    def create_judge_provider(self) -> BaseJudgeProvider:
        if settings.llm_provider == "openai":
            return OpenAIJudgeProvider()
        if settings.llm_provider == "anthropic":
            return AnthropicJudgeProvider()
        raise ProviderError(f"Unsupported provider: {settings.llm_provider}")
