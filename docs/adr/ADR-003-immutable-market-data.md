# ADR-003 — Raw market data append-only

Status: Accepted · Date: 2026-09-18

## Context
Los backtests deben ser reproducibles y auditables.

## Decision
Candles se insertan con constraint de unicidad; las correcciones requieren un nuevo proceso explícito, no mutación silenciosa.

## Alternatives considered
Actualizar filas in place.

## Consequences
La calidad de datos se valida antes de ejecutar análisis.
