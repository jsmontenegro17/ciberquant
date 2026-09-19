# ADR-005 — Git development workflow

Status: Accepted · Date: 2026-09-18

## Context
CiberQuant inició su historial dentro de la rama de REQ-001 y necesita un flujo estable para trabajo multiagente.

## Decision
`main` representa siempre el estado integrado estable. Cada requerimiento posterior usa una rama `codex/req-XXX-description`, Pull Request, CI exitoso y QA antes de merge. REQ-001 es una excepción bootstrap: una vez validado, `main` se crea apuntando al mismo SHA final, preservando historial.

## Alternatives considered
Continuar usando la rama del primer requerimiento como default; crear una historia artificial de PR previa al bootstrap.

## Consequences
El primer PR real será REQ-002. La rama bootstrap se conserva hasta verificar que `main`, CI y documentación están correctos. Branch protection se recomienda cuando la configuración del repositorio lo permita.
