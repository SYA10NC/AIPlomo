FROM ghcr.io/astral-sh/uv:0.13.0 AS uv
FROM python:3.12-slim

COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
RUN uv sync --locked --no-dev --no-editable

ENTRYPOINT ["instagram-analysis"]
CMD ["--help"]
