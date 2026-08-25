import re
from dataclasses import dataclass

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from core.config import settings
from core.exceptions import ProviderError

_JUDGE_SYSTEM = (
    "You are a retrieval quality judge. Given a question, a generated answer, "
    "and the retrieved context used to produce that answer, score how well the "
    "answer is grounded in the context on a scale from 0.0 to 1.0.\n\n"
    "Scoring guide:\n"
    "  1.0 — answer is fully supported by the context with no unsupported claims\n"
    "  0.7 — answer is mostly supported; minor gaps or inferences\n"
    "  0.4 — answer partially supported; some claims lack context evidence\n"
    "  0.0 — answer is not supported by the context or contradicts it\n\n"
    "Reply with exactly two lines:\n"
    "Score: <float between 0.0 and 1.0>\n"
    "Rationale: <one sentence>"
)


def _build_judge_prompt(prompt: str, answer: str, context: str) -> str:
    return (
        f"Question:\n{prompt}\n\n"
        f"Retrieved Context:\n{context}\n\n"
        f"Generated Answer:\n{answer}"
    )


def _parse_judge_response(text: str) -> tuple[float, str]:
    score_match = re.search(r"Score:\s*([0-9.]+)", text)
    rationale_match = re.search(r"Rationale:\s*(.+)", text)
    score = float(score_match.group(1)) if score_match else 0.0
    score = max(0.0, min(1.0, score))
    rationale = rationale_match.group(1).strip() if rationale_match else text.strip()
    return score, rationale


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
        response = await self.client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.0,
            max_tokens=128,
            messages=[
                {"role": "system", "content": _JUDGE_SYSTEM},
                {"role": "user", "content": _build_judge_prompt(prompt, answer, context)},
            ],
        )
        text = response.choices[0].message.content or ""
        score, rationale = _parse_judge_response(text)
        return JudgeResult(score=score, rationale=rationale)


class AnthropicJudgeProvider(BaseJudgeProvider):
    def __init__(self) -> None:
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def judge_retrieval(self, prompt: str, answer: str, context: str) -> JudgeResult:
        response = await self.client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=128,
            temperature=0.0,
            system=_JUDGE_SYSTEM,
            messages=[{"role": "user", "content": _build_judge_prompt(prompt, answer, context)}],
        )
        text = response.content[0].text if response.content else ""
        score, rationale = _parse_judge_response(text)
        return JudgeResult(score=score, rationale=rationale)


class LLMProviderFactory:
    def create_judge_provider(self) -> BaseJudgeProvider:
        if settings.llm_provider == "openai":
            return OpenAIJudgeProvider()
        if settings.llm_provider == "anthropic":
            return AnthropicJudgeProvider()
        raise ProviderError(f"Unsupported provider: {settings.llm_provider}")
