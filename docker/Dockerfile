# --- Stage: Builder ---
FROM python:3.12-slim AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/opt/poetry" \
    PATH="/opt/poetry/bin:$PATH"

WORKDIR /build
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=8.14.1-2+deb13u2 ca-certificates=20250419 make=4.4.1-2 \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-root


# --- Stage: Dev ---
FROM builder AS dev

RUN poetry install --no-root
WORKDIR /app
ENV PYTHONPATH=/app

COPY alembic.ini pytest.ini ./
COPY config/ ./config/
COPY tests/ ./tests/
COPY src/ ./src/
COPY Makefile .

CMD ["make", "run"]

# --- Stage: Runtime ---
FROM python:3.12-slim AS prod

RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY alembic.ini ./
COPY config/ ./config/
COPY src/ ./src/

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

USER appuser

CMD ["python", "src/app.py"]
