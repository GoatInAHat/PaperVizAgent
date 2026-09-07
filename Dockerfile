# syntax=docker/dockerfile:1
FROM node:24-alpine AS web
WORKDIR /app
COPY web/package.json web/package-lock.json ./web/
RUN npm -C web ci
COPY web ./web
RUN npm -C web run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN uv sync --no-dev

FROM python:3.12-slim-bookworm
LABEL io.modelcontextprotocol.server.name="io.github.GoatInAHat/papervizagent"
WORKDIR /app
COPY --from=build /app/.venv ./.venv
COPY --from=build /app/src ./src
COPY --from=build /app/pyproject.toml ./
COPY --from=web /app/web/dist ./src/papervizagent/web
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["python","-m","papervizagent.toolfactory.mcp"]
