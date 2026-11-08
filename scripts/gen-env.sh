#!/usr/bin/env bash
# Генерирует .env для prod из example.env с новыми случайными секретами.
# Если .env уже существует — ничего не делает и использует его.
#
# Значения можно передать через переменные окружения:
#   BOT_TOKEN=123:abc WEBHOOK_HOST=bot.example.com scripts/gen-env.sh
# BOT_TOKEN не генерируется: если не передан, остаётся заглушка из example.env.
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE=".env"
TEMPLATE="example.env"

if [ -f "$ENV_FILE" ]; then
  echo "$ENV_FILE уже существует, используем его"
  exit 0
fi

secret() {
  # только [A-Za-z0-9]: безопасно для URL подключения к postgres
  # tr получает SIGPIPE от head — с pipefail это ошибка, поэтому || true
  (LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "${1:-32}") || true
}

# set_var KEY VALUE — заменяет строку KEY=... (в том числе закомментированную) или дописывает в конец
set_var() {
  local key="$1" value="$2" tmp
  tmp="$(mktemp)"
  awk -v k="$key" -v v="$value" '
    BEGIN { done = 0 }
    !done && $0 ~ "^#? *" k "=" { print k "=" v; done = 1; next }
    { print }
    END { if (!done) print k "=" v }
  ' "$ENV_FILE" >"$tmp"
  mv "$tmp" "$ENV_FILE"
}

# unset_var KEY — комментирует строку KEY=...
unset_var() {
  local key="$1" tmp
  tmp="$(mktemp)"
  awk -v k="$key" '$0 ~ "^" k "=" { print "# " $0; next } { print }' "$ENV_FILE" >"$tmp"
  mv "$tmp" "$ENV_FILE"
}

cp "$TEMPLATE" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# секреты; postgres-контейнер читает тот же .env и создаёт БД с этими данными
set_var POSTGRES_USER olgram
set_var POSTGRES_DB olgram
set_var POSTGRES_PASSWORD "$(secret 32)"
set_var TOKEN_ENCRYPTION_KEY "$(secret 32)"

# адреса сервисов внутри docker compose
set_var POSTGRES_HOST postgres
set_var REDIS_PATH redis://redis

# за traefik: Let's Encrypt-сертификат, вебхук на 443, самоподписанный сертификат не нужен
set_var WEBHOOK_PORT 443
unset_var CUSTOM_CERT

[ -n "${BOT_TOKEN:-}" ] && set_var BOT_TOKEN "$BOT_TOKEN"
[ -n "${WEBHOOK_HOST:-}" ] && set_var WEBHOOK_HOST "$WEBHOOK_HOST"

echo "Создан $ENV_FILE с новыми секретами"
grep -q '^BOT_TOKEN=YOUR_BOT_TOKEN_HERE' "$ENV_FILE" && echo "  ! заполните BOT_TOKEN"
grep -q '^WEBHOOK_HOST=YOUR_HOST_HERE' "$ENV_FILE" && echo "  ! заполните WEBHOOK_HOST"
echo "  ! сохраните TOKEN_ENCRYPTION_KEY: без него токены ботов не восстановить"
