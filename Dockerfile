FROM python:3.12-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1

RUN apt-get update && \
    apt-get install -y gettext build-essential && \
    apt-get clean && rm -rf /var/cache/apt/* && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*

COPY . /app
WORKDIR /app

RUN uv sync --locked

RUN msgfmt locales/zh/LC_MESSAGES/olgram.po -o locales/zh/LC_MESSAGES/olgram.mo --use-fuzzy
RUN msgfmt locales/uk/LC_MESSAGES/olgram.po -o locales/uk/LC_MESSAGES/olgram.mo --use-fuzzy
RUN msgfmt locales/en/LC_MESSAGES/olgram.po -o locales/en/LC_MESSAGES/olgram.mo --use-fuzzy

EXPOSE 80

ENTRYPOINT ["./docker-entrypoint.sh"]
