# Runbook

## Read-only scanner (REQ-007)

Upgrade to migration006 before starting `python -m app.live.worker` from backend. For Docker Replay use `ENABLE_REPLAY_PROVIDER=true` in API/worker environments and `docker compose --profile scanner up --build`; default Compose leaves worker/profile and providers disabled. Worker waits for backend migration/health. PostgreSQL advisory singleton prevents multiple owners; do not also run a terminal worker against that database.

Configure `LIVE_STALE_FACTOR` (default2 × timeframe), clock drift30s, heartbeat15s and poll1s; heartbeat must exceed normal polling interval. `REPLAY_PREFIX_CANDLES`, `REPLAY_SPEED` (1x/10x/MAX) and optional synthetic `REPLAY_PAYOUT` are development-only. API and worker must share provider/health settings. MT5 runs separately on a configured Windows terminal host, not the Linux core image: [setup](providers/MT5.md).

Create watchlist/item in `/scanner`; no orders or financial mutations. Provider failures retry with bounded exponential backoff. DATA_CONFLICT is latched: inspect provenance/raw values and correct the feed/configuration before restarting worker, never overwrite raw candles. Restart marks unfinished paper observations UNAVAILABLE and rebuilds canonical feature state without retrospective LIVE signals. Export scanner events/outcomes/provenance before downgrade006 (which destroys those derived tables but preserves raw candles/financial data).

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
