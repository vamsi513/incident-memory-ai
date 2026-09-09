"""
Real-LLM tests for app/main.py's citation and no-answer behavior.

Unlike the rest of the suite, these make genuine paid API calls (whichever
provider LLM_PROVIDER/openai_api_key etc. resolve to) -- that's the actual
thing being verified here (does the model really cite, does it really
refuse), so mocking the LLM call would test nothing real. Skipped
automatically if no provider key is configured.
"""

import pytest

from app.generator import build_citations, build_user_prompt
from app.llm import generate_answer
from app.prompts import SYSTEM_PROMPT
from core.config import settings
from retrieval.pipeline import run_retrieval

pytestmark = pytest.mark.skipif(
    not (settings.openai_api_key or settings.anthropic_api_key or settings.mistral_api_key),
    reason="no LLM provider API key configured -- these tests make real paid API calls",
)


def _ask(query: str) -> tuple[str, list[str]]:
    chunks = run_retrieval(query, top_k=5)
    answer = generate_answer(SYSTEM_PROMPT, build_user_prompt(query, chunks))
    citations = build_citations(chunks)
    return answer, citations


def test_answerable_query_cites_a_real_source():
    answer, citations = _ask(
        "Why did push notifications stop being delivered after a certificate rotation?"
    )
    assert citations, "expected at least one citation to be available"
    assert any(f"[{i}]" in answer for i in range(1, len(citations) + 1)), (
        f"answer did not cite any retrieved source: {answer!r}"
    )
    assert "certificate" in answer.lower() or "renewal" in answer.lower()


def test_multi_hop_query_cites_more_than_one_document():
    answer, citations = _ask(
        "Which documents together explain why a scheduled job can stop running "
        "silently and describe a real case where that happened?"
    )
    cited_indices = {i for i in range(1, len(citations) + 1) if f"[{i}]" in answer}
    cited_doc_ids = {
        citations[i - 1].split(" - path: ")[-1].split("/")[-1].removesuffix(".md")
        for i in cited_indices
    }
    assert len(cited_doc_ids) >= 2, f"expected citations spanning >=2 documents, got {cited_doc_ids}"


@pytest.mark.parametrize(
    "out_of_corpus_query",
    [
        "What is our policy for handling GDPR data subject deletion requests?",
        "What ingredients are in the recipe for the cafeteria's Friday lunch special?",
    ],
)
def test_out_of_corpus_query_triggers_no_answer_path(out_of_corpus_query):
    answer, _citations = _ask(out_of_corpus_query)
    assert answer.strip() == "I don't know based on the retrieved incident memory.", (
        f"expected the exact no-answer phrase, got: {answer!r}"
    )
