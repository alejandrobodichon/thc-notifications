# Notifications API

Notification management system for authenticated users. Each user can create notifications and send them through email, SMS or push, each channel with its own delivery logic.

## Badges

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/alejandrobodichon/thc-notifications/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/alejandrobodichon/thc-notifications/tree/main) [![Coverage Status](https://coveralls.io/repos/github/alejandrobodichon/thc-notifications/badge.svg?branch=main)](https://coveralls.io/github/alejandrobodichon/thc-notifications?branch=main)

## Decisions taken

- Clean Architecture: dependencies point inwards. Routers (presentation) call services (use cases), which depend on core abstractions (enums, exceptions, the channel interface). Repositories and clients are adapters to the database and the queue.
- Strategy pattern for channels: each channel implements `validate` and `send`, and is resolved through a registry. Adding a channel means adding one class, without modifying existing logic.
- Channel-specific recipient data (email, phone number, device token) is stored in a JSONB column and validated by each channel before saving. New channels don't require migrations.
- Each notification tracks its delivery status (`pending`, `sent`, `failed`) and send date.
- SMS is sent asynchronously through a queue (SQS, ElasticMQ locally) consumed by a separate worker, which reports the result back through an internal endpoint protected with an API key. Failed messages are retried and then moved to a dead-letter queue.
- If the queue is unavailable, the notification is stored as `failed` instead of failing the request.
- JWT authentication. Users can only modify or delete their own account; requests on other ids return `403`, so ids can't be enumerated.
- Domain exceptions grouped by category and mapped to HTTP status codes in one place.
- Alembic migrations, applied by a dedicated service before the API starts.
- Integration tests against a real PostgreSQL, with each test rolled back. The queue is replaced by a spy, so tests don't need SQS.
- Multi-stage Docker images running as a non-root user, with locked dependencies. CI runs lint, type checking and tests for both services.

## Features

- [x] User registration and login with access token.
- [x] Create a notification and send it through email, SMS or push.
- [ ] List own notifications.
- [ ] Update a notification.
- [ ] Delete a notification.

## Table of contents

- [Technology](#technology)
- [Routes](#routes)
- [Prerequisites](#prerequisites)
- [Run the app](#run-the-app)
- [Run tests](#run-tests)
- [Things to improve](#things-to-improve)

## Technology

- Language: Python 3.14
- Framework: FastAPI
- Database: PostgreSQL, SQLAlchemy (async), Alembic
- Queue: Amazon SQS (ElasticMQ locally)
- Package manager: uv
- Tests: pytest
- Lint and types: ruff, mypy
- Containers: Docker, Docker Compose
- CI: CircleCI

## Routes

API swagger: http://localhost:8000/docs

Queue UI: http://localhost:9325

## Prerequisites

- Docker and Docker Compose installed.
- `make` (preinstalled on macOS and Linux).
- No services running on localhost ports 8000, 5432, 9324 and 9325.

## Run the app

Copy the environment files and run the app:

```bash
cp .env.example .env
cp api/.env.example api/.env
make up
```

Go to http://localhost:8000/docs to test the app.

Press `Control + C` to stop the app.

## Run tests

```bash
docker compose up -d db
docker compose exec db createdb -U postgres test_thc
cd api && uv run pytest
cd ../sms-service && uv run pytest
```

Tests run in their own database, so they don't touch the app data.

## Things to improve

- Outbox pattern, so a crash between saving and publishing can't leave a notification without its queue message.
- A periodic job that marks notifications stuck in `pending` as `failed`.
- Send email and push asynchronously through queues, like SMS.
- Replace the simulated delivery with real providers.

## Author

Alejandro

- GitHub: https://github.com/alejandrobodichon
- LinkedIn: https://www.linkedin.com/in/alejandrobodichon/