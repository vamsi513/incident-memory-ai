import pytest

from eval.ragas_runner import run_retrieval_eval


@pytest.mark.asyncio
async def test_retrieval_eval_report_has_perfect_demo_hit_rate():
    report = await run_retrieval_eval()

    assert report.total_samples == 3
    assert report.average_hit_rate == 1.0
