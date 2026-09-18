# ADR-002 — FastAPI + SQLAlchemy 2

Status: Accepted · Date: 2026-09-18

## Context
Se necesita API tipada, modular y compatible con Python 3.12.

## Decision
FastAPI, Pydantic y SQLAlchemy 2 con Alembic.

## Alternatives considered
Django REST, Flask.

## Consequences
Contratos HTTP explícitos y separación entre modelos, schemas y servicios.
