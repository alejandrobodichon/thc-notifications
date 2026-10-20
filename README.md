# Users & Pokémon API

Users CRUD integrated with [PokeAPI](https://pokeapi.co). Each user can own Pokémon; only their ids are stored, and names are fetched from PokeAPI when reading users.

## Badges

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/alejandrobodichon/fastapi-take-home-challenge/tree/master.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/alejandrobodichon/fastapi-take-home-challenge/tree/master) [![Coverage Status](https://coveralls.io/repos/github/alejandrobodichon/fastapi-take-home-challenge/badge.svg?branch=master)](https://coveralls.io/github/alejandrobodichon/fastapi-take-home-challenge?branch=master)

## Decisions taken

- Layered architecture: router → service → repository / client. Routers handle HTTP, services hold business rules, repositories access the database and the client talks to PokeAPI.
- The PokeAPI client sits at the same level as the repositories: both are adapters to the outside. Only the service orchestrates them.
- Domain exceptions grouped by category (not found, conflict, external service) and mapped to HTTP status codes in one place.
- Pokémon ids stored in a relation table with a composite primary key, preventing duplicates. Adding Pokémon is idempotent.
- Every Pokémon is validated against PokeAPI before saving: if one is invalid, nothing is stored.
- PokeAPI requests are deduplicated and run concurrently. Listing users avoids N+1 queries.
- Usernames and emails are normalized to lowercase; uniqueness is also enforced by database constraints.
- Alembic migrations, applied by a dedicated service before the API starts.
- Integration tests against a real PostgreSQL, with each test rolled back. PokeAPI is simulated at the transport level, so the real client code is tested.
- Multi-stage Docker image running as a non-root user, with locked dependencies.
- FastAPI was chosen for its async support, dependency injection and automatic OpenAPI docs.

## Features

- [x] Users CRUD.
- [x] Add Pokémon to a user.
- [x] Get users with their Pokémon (id and name).

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
- Package manager: uv
- Tests: pytest
- Containers: Docker, Docker Compose
- CI: CircleCI

## Routes

API swagger: http://localhost:8000/docs

## Prerequisites

- Docker and Docker Compose installed.
- `make` (preinstalled on macOS and Linux).
- No services running on localhost ports 8000 and 5432.

## Run the app

Copy the environment file and run the app:

```bash
cp .env.example .env
make up
```

Go to http://localhost:8000/docs to test the app.

Press `Control + C` to stop the app.

## Run tests

```bash
make test
```

Tests run in their own temporary database, so they don't touch the app data.

## Things to improve

- Authentication, so users can only modify their own data.
- Cache PokeAPI responses, since Pokémon data doesn't change.
- Retries with backoff when PokeAPI fails.
- If PokeAPI is down, listing users fails; it could return only the ids instead.
- Build the Docker image in CI.

## Author

Alejandro

- GitHub: https://github.com/alejandrobodichon
- LinkedIn: https://www.linkedin.com/in/alejandrobodichon/
