# REQ-009 — Español y primeros pasos

Status: QA
Human Acceptance: PENDING
Fecha: 2026-09-21

## Solicitud

El usuario no comprende cómo empezar y solicita la interfaz en español.
La autorización cubre experiencia de uso y textos, no nuevas reglas financieras.

## Alcance

- Español como idioma de presentación; conservar rutas, contratos API, códigos de evidencia, nombres escritos por usuarios y valores enviados al backend.
- Guía de primeros pasos accesible desde navegación y resumen, separando investigación de registro manual de operaciones.
- Explicar los prerrequisitos reales, estados vacíos y límites de IQ Option: experimental, PRACTICE, solo lectura, sin órdenes ni garantía de rentabilidad.
- No afirmar que existe un formulario para crear cuentas cuando esta versión solo permite consultarlas.
- Sin traducción automática de evidencia JSON, cambios de motores, migraciones o operaciones sobre datos de producción.
- Menú móvil desplegable con texto legible; el estilo anterior ocultaba las etiquetas a menos de700px.

## Aceptación

1. Acceso, navegación y pantallas de producto muestran español comprensible.
2. Un usuario nuevo puede encontrar qué hacer primero sin crear saldos, estrategias o datos ficticios automáticamente.
3. Opciones traducidas conservan sus valores de API; etiquetas accesibles y errores comunes en español.
4. Pruebas de interfaz, lint, tipos y compilación; evidencia de CI/QA antes de merge.
5. No desplegar cambios incompletos ni dar por aprobada la revisión humana.

## Entrega

Rama: `codex/req-009-espanol-primeros-pasos`. Flujo ADR-005: PR → CI → QA → merge. Publicación posterior, sin modificar directamente la versión estable.

## Evidencia local

2026-09-21: lint, typecheck y compilación PASS.65 pruebas unitarias de interfaz PASS.8 recorridos E2E con API real y base SQLite temporal PASS (incluyen guía/móvil, importación, indicadores, estrategias, seguimiento, sesiones, validación y trazabilidad). Los recorridos conservan las verificaciones de payload, límites, ledger y resultados numéricos.

Revisión visual de capturas de escritorio y móvil. Archivos reproducibles en `frontend/test-results/req009-primeros-pasos-*.png` (ignorados por Git). Advertencias preexistentes: bundle superior a500kB y passlib/bcrypt en el entorno de prueba; no se cambian dependencias para silenciarlas.

Se traduce la presentación, no los nombres del usuario, contratos CSV/API, identificadores de motores ni evidencia JSON. Los detalles técnicos desconocidos se conservan con una introducción en español. La guía no crea datos, estrategias, seguimientos ni cuentas; no se toca producción. Versión estable1.0.0 sin promover ni etiquetar.

## Revisión humana pendiente

Validar que «Primeros pasos» permite elegir un camino, que el menú se entiende y que la distinción entre simulación y operación real queda clara. Solo después de CI verde y aceptación proceder con merge/publicación coordinada; no se declara DONE ni aceptación automática.
