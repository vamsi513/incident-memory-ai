"""
eval/mlflow_tracker.py — MLflow experiment tracking for IncidentMemory eval.

Wraps run_retrieval_eval() with MLflow so every evaluation run is tracked:
metrics (hit_rate), parameters (embed model, reranker, git SHA), and the
full report JSON saved as an artifact.

Usage:
    python -m eval.mlflow_tracker

Configuration:
    MLFLOW_TRACKING_URI — MLflow server URI (default: local ./mlruns)
    MLFLOW_EXPERIMENT   — Experiment name (default: incident-memory-eval)
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timezone

from eval.ragas_runner import run_retrieval_eval

logger = logging.getLogger(__name__)

_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "incident-memory-eval")
_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "")

try:
    import mlflow
    _MLFLOW_AVAILABLE = True
except ImportError:
    _MLFLOW_AVAILABLE = False
    logger.warning("mlflow not installed — run: pip install mlflow")


def _git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _setup_mlflow() -> None:
    if not _MLFLOW_AVAILABLE:
        return
    if _TRACKING_URI:
        mlflow.set_tracking_uri(_TRACKING_URI)
    mlflow.set_experiment(_EXPERIMENT)


async def run_eval_with_mlflow() -> dict:
    """
    Run retrieval evaluation and log all results to MLflow.

    Returns:
        Report dict with average_hit_rate and per-sample results.
    """
    report = await run_retrieval_eval()
    report_dict = report.model_dump()

    if not _MLFLOW_AVAILABLE:
        logger.info(
            "MLflow unavailable — results: avg_hit_rate=%.3f", report.average_hit_rate
        )
        return report_dict

    _setup_mlflow()

    run_name = f"eval-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    with mlflow.start_run(run_name=run_name):
        mlflow.log_params({
            "embed_model": getattr(__import__("core.config", fromlist=["settings"]).settings, "embed_model", "all-MiniLM-L6-v2"),
            "reranker": "ms-marco-MiniLM-L-6-v2",
            "retrieval_strategy": "hybrid_bm25_dense_rrf",
            "git_sha": _git_sha(),
        })

        mlflow.log_metric("average_hit_rate", report.average_hit_rate)
        mlflow.log_metric("total_samples", report.total_samples)

        for i, result in enumerate(report.results):
            mlflow.log_metric(f"sample_{i}_hit_rate", result.hit_rate)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="eval_report_"
        ) as f:
            json.dump(report_dict, f, indent=2)
            tmp_path = f.name

        mlflow.log_artifact(tmp_path, artifact_path="eval_report")
        os.unlink(tmp_path)

        logger.info(
            "MLflow run '%s' logged — avg_hit_rate=%.3f", run_name, report.average_hit_rate
        )

    return report_dict


if __name__ == "__main__":
    result = asyncio.run(run_eval_with_mlflow())
    print(json.dumps(result, indent=2))
