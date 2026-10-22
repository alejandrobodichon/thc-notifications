FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .

FROM builder AS test

RUN uv sync --locked
CMD ["uv", "run", "pytest"]

FROM python:3.14-slim AS prod

RUN useradd --create-home appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PORT=9324

USER appuser
EXPOSE 9324

CMD ["python", "worker.py"]