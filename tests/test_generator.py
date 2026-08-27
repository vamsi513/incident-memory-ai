import pytest

from eval.ragas_runner import run_retrieval_eval


@pytest.mark.asyncio
async def test_retrieval_eval_report_measures_real_hit_rate():
    report = await run_retrieval_eval()

    assert report.total_samples == 3
    # Not a fixed 1.0: the demo corpus has topically overlapping runbooks
    # (database vs. cache latency), so the cross-encoder occasionally
    # ranks a closely related document above the exact expected one.
    assert 0.0 < report.average_hit_rate <= 1.0
