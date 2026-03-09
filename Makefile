# Переменные проекта
PYTHONPATH_APP := .
PYTHON := python3
PYTEST := $(PYTHON) -m pytest
DC_DEV := docker compose -f ./docker/docker-compose.dev.yaml
ENV_FILE := config/.env

# Переменные docker
IMAGE_NAME = cust_dev_ai_app
VERSION = $(shell git rev-parse --short HEAD || echo "latest")
REGISTRY = victorbratko
IMAGE_TAG = $(REGISTRY)/$(IMAGE_NAME):$(VERSION)

.PHONY: help install-lint lint tests unit integration up down logs

## help: Показать это сообщение
help:
	@echo "Доступные команды:"
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

## run: Развернуть локально fast api сервер согласно конфигурационному файлу
run:
	PYTHONPATH=$(PYTHONPATH_APP) python src/app.py

## login: Авторизация в Docker Hub
login:
	docker login -u victorbratko

## build: Собрать образ приложения для прода
build:
	docker build \
		--target prod \
		-t $(IMAGE_TAG) \
		-t $(REGISTRY)/$(IMAGE_NAME):latest \
		-f ./docker/Dockerfile .

## push: Отправить образ в Docker Hub/Registry
push:
	docker push $(IMAGE_TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):latest

## up: Запустить dev-окружение (подгружает .env автоматически через compose)
up:
	VERSION=$(VERSION) $(DC_DEV) --env-file $(ENV_FILE) up -d --build

## down: Остановить dev-окружение
down:
	$(DC_DEV) --env-file $(ENV_FILE) down

## logs: Посмотреть логи БД (или другого сервиса)
logs:
	$(DC_DEV) --env-file $(ENV_FILE) logs -f app
