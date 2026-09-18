# Runbook

## Compose
`Copy-Item .env.example .env`; `docker compose up --build`. Detener con `docker compose down`; resetear datos con `docker compose down -v` (destructivo para la base local).

## Local
Backend: `cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; alembic upgrade head; python -m app.seed; uvicorn app.main:app --reload`.
Frontend: `cd frontend; npm install; npm run dev`.

## Diagnóstico
`GET /health`, `GET /ready`; revisar logs de Compose. El seed usa `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD`; nunca guardar esos valores reales en Git.
