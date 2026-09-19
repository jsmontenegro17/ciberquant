# Runbook

## Compose
`Copy-Item .env.example .env`; `docker compose up --build`. Detener con `docker compose down`; resetear datos con `docker compose down -v` (destructivo para la base local).

## Local
Backend: `cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; alembic upgrade head; python -m app.seed; uvicorn app.main:app --reload`.
Frontend: `cd frontend; npm install; npm run dev`.

## Diagnóstico
`GET /health`, `GET /ready`; revisar logs de Compose. El seed usa `SEED_ADMIN_EMAIL` y `SEED_ADMIN_PASSWORD`; nunca guardar esos valores reales en Git.

## GitHub Actions y bootstrap de `main`
Si el repositorio no muestra ejecuciones en Actions, un administrador debe revisar `GitHub → Settings → Actions → General → Actions permissions` y habilitar la ejecución de workflows. Después puede abrir `Actions → CI → Run workflow` sobre `codex/req-001-ciberquant-foundation`.

REQ-001 no se simula mediante un PR histórico: es la excepción bootstrap. Sólo después de un run CI exitoso se crea `main` apuntando al SHA validado, se configura como default branch y se conserva la rama de REQ-001 hasta verificar historial, CI y documentación. Desde REQ-002 se exige Pull Request y CI antes de merge. Se recomienda proteger `main` con PR obligatorio, checks exitosos, rama actualizada y sin force-push/delete.
