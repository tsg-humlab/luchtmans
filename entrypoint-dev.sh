#!/bin/sh

# Creating diretories here instead of in Dockerfile for backwards compatibility
mkdir /app/writable/media
mkdir /app/writable/log

python manage.py runserver 0.0.0.0:${DJANGO_PORT}