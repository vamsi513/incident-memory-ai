FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY core ./core
COPY services ./services
COPY schemas ./schemas
COPY workers ./workers
COPY eval ./eval
COPY tests ./tests
COPY README.md Makefile .env.example ./

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
