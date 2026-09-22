# REQ-010 — Seguimiento visual

Status: QA

## Ampliación autorizada2026-09-22

El titular solicita resolver la confusión y delega la solución. Se amplía la entrega con una vista inicial sencilla de seguimientos existentes (incluidos los de investigación, sin habilitar creación en ese modo por defecto), estado y siguiente paso en lenguaje cotidiano, ficha de conflicto y conservación del diagnóstico de futuras revisiones. Esta ampliación sustituye la restricción inicial de solo frontend únicamente para guardar diagnósticos saneados en el JSON de salud ya existente; no cambia motores, criterios de cierre, esquema ni política ADR-006. No promete recuperar el segundo precio perdido del incidente2026-09-21 ni reactivar la suscripción bloqueada. La limitación del proveedor sigue abierta: recuperar señales exige una política versionada separada, no un retraso arbitrario ni borrar el bloqueo.

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

### Verificación de la ampliación2026-09-22

73 pruebas frontend PASS; 204 backend PASS/22 skips explícitos locales; 8 E2E con API real PASS y una prueba visual adicional de conflicto con respuestas controladas PASS. Diagnóstico de IQ con transporte falso: conserva ambos cierres en salud, sobrevive reinicio, queda privado por las comprobaciones de propiedad existentes, no reescribe velas ni crea eventos extra. Sin conexión a IQ real durante las pruebas. Lint/typecheck/build PASS. Capturas del estado bloqueado en `frontend/test-results/req010-conflict-desktop.png` y `req010-conflict-mobile.png`. El titular delegó la solución de interfaz; no equivale a declarar resuelta la limitación de finalización del proveedor.
