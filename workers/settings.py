from arq.connections import RedisSettings

from core.config import settings
from workers.tasks import run_eval_job, run_ingestion_job


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [run_ingestion_job, run_eval_job]
