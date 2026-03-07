# Переменные проекта
PYTHONPATH_APP := .
PYTHON := python3
PYTEST := $(PYTHON) -m pytest
DC_DEV := docker compose -f ./docker/docker-compose.dev.yaml
ENV_FILE := config/.env

# Цвета для вывода (для красоты)
YELLOW := $(shell tput setaf 3)
RESET  := $(shell tput sgr0)

.PHONY: help install-lint lint tests unit integration up down logs

## help: Показать это сообщение
help:
	@echo "$(YELLOW)Доступные команды:$(RESET)"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'


## install-lint: Установить pre-commit хуки
install-lint:
	pre-commit install

## lint: Запустить линтеры на всех файлах
lint:
	pre-commit run --all-files

## test: Запустить все тесты
tests:
	$(PYTEST) -vv tests

## unit: Запустить только unit-тесты
unit:
	$(PYTEST) -vv tests/unit

## integration: Запустить только integration-тесты
integration:
	$(PYTEST) -vv tests/integration

## add_migration: Добавить автогенерируемую миграцию с помощью alembic (важно потом провалидировать правильность миграций!)
add_migration:
	PYTHONPATH=$(PYTHONPATH_APP) alembic revision --autogenerate

## roll_up_migrations: Накатить на базу данных последнию добавленную миграцию
roll_up_migrations:
	PYTHONPATH=$(PYTHONPATH_APP) alembic upgrade head

## up: Запустить dev-окружение (подгружает .env автоматически через compose)
up:
	$(DC_DEV) --env-file $(ENV_FILE) up -d

## down: Остановить dev-окружение
down:
	$(DC_DEV) down

## logs: Посмотреть логи БД (или другого сервиса)
logs:
	$(DC_DEV) logs -f db
