import pytest

from core.tracing import traced_span


def test_logs_stage_timing_on_normal_exit(caplog):
    with caplog.at_level("INFO", logger="core.tracing"):
        with traced_span("fake_stage"):
            pass

    assert any("stage_timing stage=fake_stage" in r.message for r in caplog.records)


def test_logs_stage_timing_even_when_body_raises(caplog):
    with caplog.at_level("INFO", logger="core.tracing"):
        with pytest.raises(RuntimeError):
            with traced_span("fake_stage"):
                raise RuntimeError("boom")

    assert any("stage_timing stage=fake_stage" in r.message for r in caplog.records)


def test_nested_spans_each_log_their_own_stage(caplog):
    with caplog.at_level("INFO", logger="core.tracing"):
        with traced_span("outer"):
            with traced_span("inner"):
                pass

    messages = [r.message for r in caplog.records]
    assert any("stage_timing stage=outer" in m for m in messages)
    assert any("stage_timing stage=inner" in m for m in messages)
