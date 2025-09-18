# Luchtmans booksellers database

The private client accounts of the Leiden booksellers firm Luchtmans (1683-1848).

## Prerequisites

This project uses [uv](https://docs.astral.sh/uv/), [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) to build and run.

## Building

To build a Docker image run the following commands in the root of this repository:

```commandline
# Compile the translation (.mo) files
uv run src/manage.py compilemessages

# Create a fresh requirements.txt
uv pip compile pyproject.toml -o src/requirements.txt

# Build the Docker image; change the name:tag for you situation
docker build -t ghcr.io/tsg-humlab/luchtmans:testing .
```

## .env file

Create a .env file that looks like this:

```env
WRITABLE_DIR=./writable
SECRET_KEY='my-secret-key'
DEBUG=False
ALLOWED_HOSTS=example.com
CSRF_TRUSTED_ORIGINS=https://example.com
MEDIA_ROOT=/home/app/writable/media
MEDIA_URL=media/
DOCKER_IMAGE=ghcr.io/tsg-humlab/luchtmans:testing
DJANGO_PORT=8000
WSGI_APP=lm_project.wsgi:application
XSENDFILE_HEADER=X-Accel-Redirect

# Database: Postgres
DATABASE=postgres
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=django_app_pg_dbname
SQL_USER=django_app_pg_user
SQL_PASSWORD=django_app_pg_password
SQL_HOST=postgres
SQL_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

## Running

Using `docker-compose.yml` and `nginx.conf` from this repository, run the following command to start the application:

```commandline
docker compose up -d
```