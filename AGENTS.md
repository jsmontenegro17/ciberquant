# CiberQuant — guía operativa

## Propósito

CiberQuant es una plataforma multiusuario de investigación cuantitativa. Backend y base de datos son la autoridad para reglas financieras; el producto no opera automáticamente.

## Arquitectura y stack

`backend/` contiene FastAPI, SQLAlchemy 2, Alembic, Pydantic y servicios de dominio. `frontend/` contiene React + TypeScript + Vite. PostgreSQL es la base objetivo y Docker Compose levanta el entorno. El catálogo operativo está en [docs/CONTEXT_INDEX.md](docs/CONTEXT_INDEX.md).

## Flujo de trabajo

1. Leer este archivo, [CONTEXT_INDEX.md](docs/CONTEXT_INDEX.md), [PROJECT_STATE.md](docs/PROJECT_STATE.md) y sólo los módulos afectados.
2. Crear o actualizar un REQ en `docs/requirements/` antes de cambios significativos.
3. Revisar ADRs aplicables, implementar en una rama `codex/req-XXX-nombre`, probar, actualizar documentación y usar Conventional Commits.
4. No mezclar OTC con regular, no usar floats para dinero, no introducir lookahead bias, martingala ni auto-trading.

## Validación

Backend: `cd backend; python -m pytest`. Frontend: `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`. Compose: `docker compose up --build`.

## Definition of Done

Acceptance criteria verificados, tests relevantes pasando, migraciones revisables, documentación sincronizada, sin secretos, y cambios trazables a un REQ. Más detalle: [docs/TESTING.md](docs/TESTING.md), [docs/RUNBOOK.md](docs/RUNBOOK.md).
