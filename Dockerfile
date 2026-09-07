# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN uv sync --no-dev

FROM python:3.12-slim-bookworm
LABEL io.modelcontextprotocol.server.name="io.github.GoatInAHat/papervizagent-codex"
WORKDIR /app
COPY --from=build /app/.venv ./.venv
COPY --from=build /app/src ./src
COPY --from=build /app/pyproject.toml ./
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["python","-m","papervizagent_codex.toolfactory.mcp"]
