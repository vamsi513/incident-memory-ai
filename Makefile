install:
	pip install -r requirements.txt -r requirements-dev.txt

run-api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	arq workers.settings.WorkerSettings

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .
