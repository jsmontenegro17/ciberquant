/** Presentation only: never use translated labels in requests or persisted evidence. */
const labels: Record<string, string> = {
  OPEN:'Abierta', CLOSED:'Cerrada', STOPPED:'Detenida', ACTIVE:'Activa', INACTIVE:'Inactiva',
  WIN:'Ganada', LOSS:'Perdida', DRAW:'Empate', CANCELLED:'Cancelada',
  CALL:'Al alza', PUT:'A la baja', C:'Vela alcista', P:'Vela bajista', D:'Doji exacto',
  REGULAR:'Regular', OTC:'Fuera del mercado regular',
  DRAFT:'Borrador', TESTING:'En prueba', DISABLED:'Deshabilitada',
  PASS:'Aprobada', FAIL:'No aprobada', INCONCLUSIVE:'No concluyente', NOT_VALIDATED:'Sin validar',
  HISTORICALLY_VALIDATED:'Validada históricamente', IN_SAMPLE_ONLY:'Solo dentro de la muestra',
  RUNNING:'En ejecución', PROCESSING:'En proceso', COMPLETED:'Completada', FAILED:'Fallida',
  SEALED:'Reservada', REVEALED:'Revelada', RUNNING_DEVELOPMENT:'Calculando desarrollo', RUNNING_TEST:'Calculando prueba',
  READY:'Evidencia disponible', MISSING:'Sin evidencia', STALE:'Sin actualización reciente',
  UNAVAILABLE:'No disponible', INCOMPATIBLE:'Incompatible', GAP:'Hueco de datos',
  MATCH:'Condiciones cumplidas', NO_MATCH:'Condiciones no cumplidas', WARMUP:'Preparación inicial',
  PROVIDER_DOWN:'Proveedor no disponible', INSUFFICIENT_HISTORY:'Histórico insuficiente',
  SUSPENDED_DEGRADED:'Suspendido por degradación', CONNECTED:'Conectado', DISCONNECTED:'Desconectado',
  DATA_CONFLICT:'Conflicto de datos: seguimiento detenido', LIVE:'En vivo', REPLAY:'Reproducción',
  EXPERIMENTAL:'Experimental', PRACTICE:'Demostración',
  ALLOW:'Permitir superposición', SKIP_UNTIL_EXPIRY:'Esperar hasta el vencimiento',
  AND:'Todas las condiciones', OR:'Alguna condición', GT:'Mayor que', GE:'Mayor o igual',
  LT:'Menor que', LE:'Menor o igual', GTE:'Mayor o igual', LTE:'Menor o igual', EQ:'Igual', NE:'Distinto',
  FIELD:'Campo', NUMBER:'Número', STRING:'Texto', BOOLEAN:'Lógico',
  DATA:'Datos', FEATURES:'Indicadores', STRATEGY:'Estrategia', BACKTEST:'Prueba histórica',
  VALIDATION:'Validación', SCANNER:'Seguimiento', PAPER:'Simulación',
  INITIAL_BALANCE:'Saldo inicial', TRADE_PROFIT:'Ganancia de operación', TRADE_LOSS:'Pérdida de operación',
};
export function codeLabel(value: string | number | null | undefined): string {
  if (value == null) return '—';
  return labels[value] ? `${labels[value]} (${value})` : String(value);
}
export const datasetLabels: Record<string,string> = {
  source:'Fuente', broker:'Bróker', symbol:'Símbolo', market_type:'Tipo de mercado', timeframe:'Temporalidad',
};
export function evidenceText(value: string | undefined): string {
  if (!value) return '';
  const known: Record<string,string> = {
    'No matching evidence':'No hay evidencia compatible',
    'Descriptive evidence only. Fixed historical assumptions and observed LIVE/REPLAY paper samples are not pooled.':'Solo evidencia descriptiva. No se combinan los supuestos históricos fijos con las simulaciones observadas en vivo o en reproducción.',
    'UNOFFICIAL COMMUNITY INTEGRATION — Protocol may change without notice.':'Integración comunitaria no oficial: el protocolo puede cambiar sin aviso.',
    'period + 1 candles':'período + 1 velas', 'period candles':'período de velas',
  };
  return known[value] ?? value.replace(/^(\d+) closed candles$/, '$1 velas cerradas')
    .replace(/^StrategyVersion #/, 'Versión de estrategia n.º')
    .replace(/^Validation #/, 'Validación n.º').replace(/^Outcome #/, 'Resultado n.º')
    .replace(/ · resolved /, ' · resueltas ').replace(/unavailable$/, 'no disponible');
}

const errors: Record<string,string> = {
  'Invalid credentials':'El correo o la contraseña no son correctos.',
  'Authentication required':'Inicia sesión para continuar.',
  'Invalid authentication':'Tu sesión ha caducado. Vuelve a iniciar sesión.',
  'Inactive user':'El usuario está inactivo. Contacta al administrador.',
  'Administrator role required':'Esta acción requiere permisos de administrador.',
  'Account not found':'No se encontró la cuenta.', 'Session not found':'No se encontró la sesión.',
  'Resource not found':'No se encontró el recurso.', 'Trade not found':'No se encontró la operación.',
  'No risk profile configured':'No tienes un perfil de riesgo configurado. Solicítalo al administrador.',
  'Account is not available for a session':'Esta cuenta no está disponible para iniciar una sesión.',
  'An active session already exists for this account':'Esta cuenta ya tiene una sesión activa.',
  'Account or session not found':'No se encontró la cuenta o la sesión.',
  'Session does not belong to account':'La sesión no pertenece a esta cuenta.',
  'Session is not open':'La sesión no está abierta.', 'SESSION LIMIT REACHED':'Se alcanzó el límite de la sesión.',
  'Stake exceeds per-trade risk limit':'El importe supera el límite de riesgo por operación.',
  'Stake exceeds balance or remaining session risk':'El importe supera el saldo o el riesgo restante de la sesión.',
  'Payout is below session minimum':'El rendimiento es inferior al mínimo de la sesión.',
  'Trade does not belong to session':'La operación no pertenece a esta sesión.',
  'Duplicate watch item':'Ya existe ese seguimiento.',
  'Research mode requires explicit paper payout/expiry assumptions':'Indica el rendimiento supuesto y el vencimiento de la simulación.',
  'HISTORICALLY_VALIDATED on the exact dataset and TESTING lifecycle required':'Se requiere validación histórica de estos datos y una estrategia en estado TESTING. Para una idea no validada usa explícitamente el modo de investigación.',
  'IQOPTION dataset required':'La fuente y el bróker deben identificar datos de IQOPTION.',
  'MT5 supports its own REGULAR datasets only; no OTC substitution':'MT5 solo admite sus propios datos REGULAR; no se sustituyen por OTC.',
  'CSV exceeds configured upload limit':'El CSV supera el tamaño permitido.',
  'Concurrent version change; retry':'La versión cambió durante la solicitud. Vuelve a intentarlo.',
  'Database unavailable':'La base de datos no está disponible.',
  'Invalid dataset context':'La identidad del conjunto de datos no es válida.',
  'Request failed':'No se pudo completar la solicitud.', 'Invalid input':'Revisa los datos introducidos.',
};
export function errorMessage(detail: string): string {
  return errors[detail] ?? `No se pudo completar la solicitud. Detalle técnico: ${detail}`;
}
