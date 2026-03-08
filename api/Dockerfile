# syntax=docker/dockerfile:1

# --- Build stage: install Poetry + dependencies into a venv ---
FROM python:3.12-slim AS build

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --only main --no-root --no-directory

COPY . .

RUN poetry install --only main

# --- Runtime stage: clean slim image with just the venv ---
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd -g 1001 app && \
    useradd -u 1001 -g app -m -s /bin/bash app

WORKDIR /app

COPY --from=build --chown=app:app /app /app

RUN mkdir -p /app/data && chown app:app /app/data

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
