# FastAPI Template

A FastAPI app template with PostgreSQL, Redis, and Celery integration, managed with uv,
allowing you to create various applications faster and more efficiently.

## Development

### Install uv

This project uses `uv` for dependency management. Make sure you have uv installed:
- For MacOS/Linux
```bash
#MacOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```
- For **Windows**
```bash
#Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.8.4/install.ps1 | iex"
```
or using pip
```bash
pip install uv
```
### Activate virtual environment and install packages

- Create .env from .env.dev-example
```bash
cp  env.dev-example .env
```

- Init virtual environment

```bash
uv venv
```

after that activate it:
```bash
#MacOS/Linux
source ./.venv/bin/activate

#Windows
./.venv/Scripts/activate
```
### Run app via Docker
```bash
docker compose up --build
```


## Services

- **App**: FastAPI application running on port 8000
- **Database**: PostgreSQL on port 5432
- **Redis**: Redis with RedisStack on port 6379
- **Celery**: Background task worker