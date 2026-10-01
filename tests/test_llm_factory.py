"""
Tests for core/llm_factory.py's judge providers.

_parse_judge_response is pure and always runs. The provider test makes a
real Bedrock call -- like tests/test_query_citations.py's real-LLM tests,
mocking the call here would only verify that a mock was set up correctly,
not that Bedrock access actually works. Skipped automatically when no AWS
credentials are configured.
"""

import boto3
import pytest

from core.exceptions import ProviderError
from core.llm_factory import BedrockJudgeProvider, LLMProviderFactory, _parse_judge_response


class TestParseJudgeResponse:
    def test_parses_score_and_rationale(self):
        score, rationale = _parse_judge_response(
            "Score: 0.7\nRationale: Mostly grounded, one unsupported detail."
        )
        assert score == 0.7
        assert rationale == "Mostly grounded, one unsupported detail."

    def test_clamps_score_to_valid_range(self):
        score, _ = _parse_judge_response("Score: 1.4\nRationale: whatever")
        assert score == 1.0

    def test_missing_score_defaults_to_zero(self):
        score, rationale = _parse_judge_response("not the expected format")
        assert score == 0.0
        assert rationale == "not the expected format"


class TestLLMProviderFactory:
    def test_unsupported_provider_raises_provider_error(self, monkeypatch):
        from core.config import settings

        monkeypatch.setattr(settings, "llm_provider", "does-not-exist")
        with pytest.raises(ProviderError):
            LLMProviderFactory().create_judge_provider()


_has_aws_credentials = boto3.Session().get_credentials() is not None


@pytest.mark.skipif(
    not _has_aws_credentials,
    reason="no AWS credentials configured -- this test makes a real Bedrock call",
)
async def test_bedrock_judge_scores_a_grounded_answer():
    provider = BedrockJudgeProvider()
    result = await provider.judge_retrieval(
        prompt="What caused the outage?",
        answer="The outage was caused by a certificate that expired without being rotated.",
        context=(
            "Incident report: the push notification service stopped delivering "
            "messages after its TLS certificate expired. The on-call engineer "
            "rotated the certificate and service resumed within 10 minutes."
        ),
    )
    assert 0.0 <= result.score <= 1.0
    assert result.rationale
