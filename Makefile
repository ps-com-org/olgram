#####
-include Makefile.inc
#####

.PHONY: docker-debug-prepare docker-prod-prepare docker-run docker-update env

# локальная разработка: только postgres + valkey, бот запускается без docker
docker-debug-prepare:
	cp -f docker-compose-debug.yaml docker-compose.yaml
	cp --update=none debug.env .env

# .env для prod с новыми секретами; если .env уже есть — используется он
# можно передать: make env BOT_TOKEN=... WEBHOOK_HOST=...
env:
	BOT_TOKEN="$(BOT_TOKEN)" WEBHOOK_HOST="$(WEBHOOK_HOST)" ./scripts/gen-env.sh

# сервер: docker-compose-prod.yaml -> docker-compose.yaml (сам файл в .gitignore)
docker-prod-prepare: env
	cp -f docker-compose-prod.yaml docker-compose.yaml

docker-run:
	docker compose up -d

# обновить docker-compose.yaml из prod, пересобрать образ и перезапустить контейнеры
docker-update: docker-prod-prepare
	docker compose build
	docker compose up -d --remove-orphans
