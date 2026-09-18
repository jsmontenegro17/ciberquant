# ADR-004 — Decimal y ledger

Status: Accepted · Date: 2026-09-18

## Context
Los errores de redondeo y balances sin historial son riesgos financieros.

## Decision
`Decimal` en Python, `NUMERIC` en PostgreSQL y entradas de ledger con balance antes/después.

## Alternatives considered
Float y balance mutable.

## Consequences
Las fórmulas financieras viven en backend y son testeadas.
