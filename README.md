# CiberQuant

Plataforma de investigación cuantitativa para trading, con foco inicial en opciones binarias. La V1 prioriza datos auditables, gestión monetaria, sesiones, journal, catalogación y backtesting determinista. No ejecuta órdenes.

## Inicio rápido

1. Copia `.env.example` a `.env`.
2. Ejecuta `docker compose up --build`.
3. API: http://localhost:8000/docs · Frontend: http://localhost:5173.

Para desarrollo local y pruebas, consulta [docs/RUNBOOK.md](docs/RUNBOOK.md).

## Estado

La implementación inicial está trazada a [REQ-001](docs/requirements/REQ-001-foundation.md). El mapa operativo está en [AGENTS.md](AGENTS.md) y [docs/CONTEXT_INDEX.md](docs/CONTEXT_INDEX.md).
