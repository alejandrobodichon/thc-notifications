TEST_COMPOSE = docker compose -p thc-test -f docker-compose.yml -f docker-compose-test.yml

up:
	docker compose up --build

dev:
	docker compose -f docker-compose.yml -f docker-compose-dev.yml up --build

test:
	$(TEST_COMPOSE) up --build --abort-on-container-exit --exit-code-from tests; \
	status=$$?; \
	$(TEST_COMPOSE) down -v; \
	exit $$status

.PHONY: up dev test