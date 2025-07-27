# Meal Application

A FastAPI application with PostgreSQL, Redis, and Celery integration, managed with uv.

## Development

This project uses `uv` for dependency management. Make sure you have uv installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Running with Docker

Build and run the application:

```bash
docker-compose up --build
```

## Project Structure

- `app/` - Application code
- `scripts/` - Shell scripts for running services
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependencies

## Services

- **App**: FastAPI application running on port 8000
- **Database**: PostgreSQL on port 5432
- **Redis**: Redis with RedisStack on port 6379
- **Celery**: Background task worker

## Environment Variables

Create a `.env` file with the following variables:

```env
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_db
REDIS_PASSWORD=your_redis_password
```