###########
# BUILDER #
###########

FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install system dependencies
RUN apk add binutils proj-dev gdal geos

# Install project dependencies
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

FROM python:3.14-alpine

ENV PATH="/app/.venv/bin:$PATH"

# Create the necessary directories
WORKDIR /app/
RUN mkdir /app/writable /app/staticfiles

# Install dependencies
RUN apk add binutils proj gdal geos

# Make libraries findable for GeoDjango
RUN ln -s /usr/lib/libgeos.so.3.13.1 /usr/lib/libgeos.so \
    && ln -s /usr/lib/libgeos_c.so.1 /usr/lib/libgeos_c.so \
    && ln -s /usr/lib/libgdal.so.36 /usr/lib/libgdal.so \
    && ln -s /usr/lib/libproj.so.25 /usr/lib/libproj.so

# Prepare 'entrypoint.sh'
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create the 'app' user
RUN addgroup app && adduser -S -G app app && chown -R app:app /app
USER app

# Copy the compiled Python packages from 'builder'
COPY --from=builder /app /app

# RUN IT!
ENTRYPOINT ["/entrypoint.sh"]