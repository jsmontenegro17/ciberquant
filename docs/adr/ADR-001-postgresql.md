# ADR-001 — PostgreSQL

Status: Accepted · Date: 2026-09-18

## Context
CiberQuant necesita NUMERIC, JSONB, constraints y crecimiento multiusuario.

## Decision
PostgreSQL es la base soportada en producción; SQLite sólo puede ser harness de tests.

## Alternatives considered
SQLite para producción, bases documentales.

## Consequences
Se requiere Compose o PostgreSQL local; las migraciones son explícitas.
