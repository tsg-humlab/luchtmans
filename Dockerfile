###########
# BUILDER #
###########

FROM python:3.13-slim-trixie AS builder

# Copy uv bin to image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install dependencies
WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev

# Install our app
COPY src/ /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

#########
# FINAL #
#########

FROM python:3.13-slim-trixie

# Copy the compiled Python packages from 'builder'
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Create the necessary directories
WORKDIR /app/
RUN mkdir /app/writable /app/staticfiles

# Prepare 'entrypoint.sh'
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create the 'app' user
RUN adduser --system --group app && chown -R app:app /app
USER app

# RUN IT!
ENTRYPOINT ["/entrypoint.sh"]