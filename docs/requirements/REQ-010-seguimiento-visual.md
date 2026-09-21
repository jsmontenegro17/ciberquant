# REQ-010 — Seguimiento visual

Status: QA

Solicitud2026-09-21: reemplazar la presentación principal en JSON por una vista limpia y visual del seguimiento existente.

## Alcance

- Solo frontend: resumen de conexión/mercado, velas observadas, última señal y resultados simulados.
- Configuración y evidencia técnica disponibles bajo secciones desplegables.
- Precios exactos conservados como texto; geometría gráfica aproximada, sin cálculos financieros nuevos.
- La instantánea contiene como máximo la última vela cerrada y la provisional: no inventar historial ni señales.
- Mantener separación proveedor conectado/mercado abierto, investigación/validación y simulación/órdenes.
- DATA_CONFLICT, desconexión, pausa o error de consulta nunca deben presentarse como señal operativa actual.
- No modificar estrategia, seguimiento, backend, datos, contratos congelados ni integración IQ Option.

## Aceptación

Vista sin JSON expandido por defecto; valores ausentes explícitos; estados de mercado cerrado/conflicto/desconexión claros; velas etiquetadas y valores accesibles; diseño móvil sin desbordamiento. Pruebas unitarias, lint, build y E2E relevantes. ADR-005/006 aplicables; PR y CI antes de integrar. Publicación y aceptación humana pendientes.

## Evidencia local

71 pruebas frontend PASS; 8 E2E con API real y datos aislados PASS. Lint y build PASS. Revisión visual de captura móvil390px: sin desbordamiento; JSON oculto por defecto. Capturas locales `frontend/test-results/req010-scanner-desktop.png` y `req010-scanner-mobile.png`.

La vista muestra hasta dos velas de la instantánea, con escalas individuales claramente advertidas. No agrega historial ni métricas de rendimiento agregadas. No modifica estado de seguimientos ni estrategia de aprendizaje existente. Al fallar la consulta no muestra velas cacheadas como actuales; pausa/conflicto/desconexión suprimen la representación en vivo y MATCH operativo. Advertencia de bundle grande preexistente.
