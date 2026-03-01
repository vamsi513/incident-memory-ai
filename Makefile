install:
	pip install -r requirements.txt -r requirements-dev.txt

run-api:
	uvicorn app.main:app --reload --port 8000

run-ui:
	streamlit run ui/streamlit_app.py

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

ingest:
	python scripts/run_ingestion.py

eval:
	python scripts/run_evals.py

