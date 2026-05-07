FROM python:3.12-slim

# Install Stockfish from apt
RUN apt-get update && apt-get install -y stockfish --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv --no-cache-dir

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --no-dev --no-cache

COPY celery_app.py .
COPY tasks/ tasks/
COPY engine/ engine/

CMD ["uv", "run", "celery", "-A", "celery_app", "worker", \
     "--loglevel=info", "--concurrency=2", \
     "--queues=ingest,analysis"]
