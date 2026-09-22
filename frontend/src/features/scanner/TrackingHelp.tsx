import type {WatchItem} from '../../api/scanner';

export function TrackingHelp({item}:{item:WatchItem}) {
 const conflict=item.latest?.error==='DATA_CONFLICT';
 const closed=item.latest?.health?.market_open===false;
 const [title,description,next]=conflict
  ? ['Detenido para proteger tus resultados','IQ Option cambió una vela que ya habíamos recibido. No es un error de tu estrategia.','No necesitas cambiar tus reglas. El seguimiento requiere revisión técnica; pausarlo o activarlo no resuelve el conflicto. Puedes consultar resultados anteriores, pero no habrá señales nuevas.']
  : !item.enabled ? ['En pausa','Tú has pausado este seguimiento.','Pulsa «Activar seguimiento» cuando quieras volver a observar. No se enviarán operaciones.']
  : closed ? ['Esperando apertura del mercado','El proveedor informa que este activo no está abierto. Recibir precios no significa que esté disponible para señales.','Puedes dejarlo configurado y revisar más tarde. No necesitas introducir dinero ni cambiar de activo.']
  : ['PROVIDER_DOWN','STALE'].includes(item.state) ? ['Sin datos actualizados','La conexión o los precios no están disponibles. No mostramos esto como una señal.','Espera datos nuevos. Si el aviso persiste, hace falta revisar la conexión del proveedor.']
  : item.state==='SUSPENDED_DEGRADED' ? ['Validación pendiente de revisión','La validación ya no permite el seguimiento normal.','Revisa la evidencia histórica antes de continuar; no cambies a investigación para ocultar el problema.']
  : item.state==='INSUFFICIENT_HISTORY' ? ['Reuniendo información','Todavía faltan velas para evaluar las reglas.','Espera a que lleguen suficientes velas cerradas. Una vela en formación no cuenta como señal.']
  : item.state==='UNAVAILABLE' ? ['Todavía no se puede evaluar','Faltan datos o condiciones necesarias para el seguimiento.','Consulta el estado de conexión debajo. No se ha confirmado una señal nueva.']
  : ['Observando tu estrategia','El sistema compara tus reglas con las velas cerradas que recibe.','Revisa las coincidencias y los resultados simulados más abajo. Una coincidencia no es una recomendación para operar.'];
 return <div className={`trackingHelp ${conflict?'blocked':''}`} role={conflict?'alert':undefined}>
  <h4>{title}</h4><p>{description}</p><p><strong>¿Qué hago ahora?</strong> {next}</p>
 </div>;
}
