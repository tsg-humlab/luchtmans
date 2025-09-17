###########
# BUILDER #
###########

# An image is based on another image, choose from e.g. https://hub.docker.com/
FROM python:3.13-slim-trixie AS builder

# System dependencies
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends gcc git

# environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Work directory
WORKDIR /django_app/

# install python dependencies
COPY src/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /django_app/wheels -r requirements.txt

#########
# FINAL #
#########

FROM python:3.13-slim-trixie
RUN apt-get update -y && apt-get upgrade -y

# Copy the compiled Python packages from 'builder'
COPY --from=builder /django_app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Create the 'app' user
RUN adduser --system --group --home /home/app app
USER app

# Create the necessary directories
RUN mkdir /home/app/writable /home/app/staticfiles
WORKDIR /home/app/
COPY src/ /home/app/

# Prepare 'entrypoint.sh'
USER root
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER app

# RUN IT!
ENTRYPOINT ["/entrypoint.sh"]