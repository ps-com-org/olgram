#####
-include Makefile.inc
#####


.Phony: docker-debug-prepare
docker-debug-prepare:
	cp -f docker-compose-debug.yaml docker-compose.yaml
	cp --update=none debug.env .env

docker-run:
	docker compose up -d