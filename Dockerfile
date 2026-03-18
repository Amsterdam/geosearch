FROM ghcr.io/astral-sh/uv:0.10-python3.14-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN apt update && apt install --no-install-recommends -y \
    build-essential \
    libpq-dev tree

WORKDIR /app
COPY ./pyproject.toml ./uv.lock ./

RUN uv sync --frozen --no-install-project --all-groups
COPY /src /app/src
COPY /tests /app/tests

RUN uv sync --frozen --all-groups

# Start runtime image,
FROM ghcr.io/astral-sh/uv:0.10-python3.14-trixie-slim

# Create user catalogus with the same UID as github actions runner.
RUN groupadd --system --gid 999  geosearch  && useradd --system --gid 999 \
    --uid 1001 --create-home geosearch
RUN apt update && apt install --no-install-recommends -y \
    curl \
    libpq5

WORKDIR /app
# Copy python build artifacts from builder image
RUN chown geosearch:geosearch /app
COPY --from=builder --chown=geosearch:geosearch /app /app
USER geosearch
# Have some defaults so the container is easier to start
ENV DJANGO_SETTINGS_MODULE=geosearch.settings \
    DJANGO_DEBUG=false

RUN uv run src/manage.py collectstatic --noinput
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT []
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "geosearch.asgi", "--host", "0.0.0.0", "--port", "8000"]
