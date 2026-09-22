import type {WatchItem} from '../../api/scanner';
import './scanner.css';

type RecordValue = Record<string, unknown>;
const record = (value:unknown):RecordValue => value && typeof value==='object' && !Array.isArray(value) ? value as RecordValue : {};
const value = (v:unknown) => typeof v==='string'||typeof v==='number' ? String(v) : 'No disponible';
export function utcTime(v:unknown){
 if(typeof v!=='string'||!Number.isFinite(Date.parse(v)))return 'Sin registro';
 return new Intl.DateTimeFormat('es-CO',{timeZone:'UTC',dateStyle:'short',timeStyle:'medium'}).format(new Date(v))+' UTC';
}
export function LiveSnapshot({item,subscription}:{item:WatchItem;subscription:{status:string;health:RecordValue;snapshot:RecordValue}|null}){
 const health=record(subscription?.health), snapshot=record(subscription?.snapshot);
 const conflict=health.error==='DATA_CONFLICT'||item.latest?.error==='DATA_CONFLICT';
 const revision=record(health.conflict);
 const connected=subscription?.status==='CONNECTED'&&health.status!=='DISCONNECTED';
 const usable=item.enabled&&connected&&!conflict;
 const candles=[{label:'Última vela cerrada',raw:record(snapshot.last_closed),provisional:false},{label:'Vela en formación',raw:record(snapshot.forming),provisional:true}];
 const message=conflict?'Detenido por conflicto de datos':!item.enabled?'Seguimiento pausado':!connected?'Esperando conexión':health.market_open===false?'Conectado · mercado cerrado':health.market_open===true?'Conectado · mercado abierto':'Conectado · apertura sin confirmar';
 return <div className="liveVisual">
  <div className="liveStatus"><span className={`liveDot ${usable&&health.market_open===true?'ready':''}`} aria-hidden="true"/><div><strong>{message}</strong><p>{conflict?'El proveedor revisó una vela. La evidencia se conserva; no se generan nuevas señales.':health.market_open===false?'Llegan datos, pero el proveedor informa que este mercado no está abierto. No se presenta como listo para señales.':'Solo observación. Una conexión no demuestra rentabilidad ni permite enviar órdenes.'}</p></div></div>
  {conflict&&<section className="conflictReport"><h4>Qué cambió en los datos</h4>{Object.keys(revision).length===0?<p>Este incidente es anterior al registro detallado: no se guardó el segundo precio. No lo reconstruimos ni suponemos cuál fue.</p>:<><p>Vela iniciada: {utcTime(revision.open_time)}</p><div className="tableWrap"><table><thead><tr><th>Precio</th><th>Primera observación</th><th>Revisión del proveedor</th></tr></thead><tbody>{[['Apertura','open'],['Máximo','high'],['Mínimo','low'],['Cierre','close']].map(([label,key])=><tr key={key}><th>{label}</th><td>{value(revision[`old_${key}`])}</td><td>{value(revision[`new_${key}`])}</td></tr>)}</tbody></table></div><p>Revisión recibida: {utcTime(revision.second_seen_received_time)}</p></>}<p>La primera vela permanece intacta. No se elige automáticamente uno de los dos precios ni se recalculan señales pasadas.</p></section>}
  {usable&&<><div className="liveMetrics"><div><span>Activo</span><strong>{item.dataset.symbol}</strong><small>{item.dataset.market_type} · {item.dataset.timeframe}</small></div><div><span>Última recepción</span><strong>{utcTime(health.last_received)}</strong></div><div><span>Rendimiento informado</span><strong>{snapshot.payout==null?'No disponible':`${value(snapshot.payout)}%`}</strong><small>No es una cotización ejecutable</small></div></div>
  <div className="liveCandles">{candles.map(({label,raw,provisional})=>{
   const prices=['open','high','low','close'].map(k=>typeof raw[k]==='string'&&raw[k]!==''?Number(raw[k]):NaN);
   const [open,high,low,close]=prices;
   const valid=prices.every(Number.isFinite)&&high>=Math.max(open,close)&&low<=Math.min(open,close);
   const range=high-low, y=(n:number)=>range===0?70:20+(high-n)/range*100;
   const direction=close>open?'Alcista':close<open?'Bajista':'Sin variación visible a esta escala';
   return <article className="liveCandle" key={label}><h4>{label}</h4><small>{provisional?'Provisional · puede cambiar':'Cerrada · no garantiza inmutabilidad del proveedor'}</small>
    {!usable||!valid?<p>Sin vela disponible para mostrar en vivo.</p>:<><div className="liveCandleBody"><svg viewBox="0 0 100 140" role="img" aria-label={`${label}: ${direction}. Representación con escala individual.`}><line x1="50" x2="50" y1={y(high)} y2={y(low)} stroke="currentColor" strokeWidth="2"/><rect x="30" width="40" y={Math.min(y(open),y(close))} height={Math.max(2,Math.abs(y(open)-y(close)))} fill={close>=open?'#3ed5b1':'#ff9a9e'} stroke="currentColor" strokeDasharray={provisional?'4 3':undefined}/></svg><dl>{[['Apertura','open'],['Máximo','high'],['Mínimo','low'],['Cierre','close']].map(([label,key])=><div key={key}><dt>{label}</dt><dd>{value(raw[key])}</dd></div>)}</dl></div><p>{direction} · {utcTime(raw.open_time)}</p></>}
   </article>;
  })}</div><p className="liveFootnote">Vista de hasta dos velas, no un gráfico histórico. Cada vela usa su propia escala; consulta los precios exactos para compararlas. La vela en formación es provisional, nunca una señal definitiva.</p></>}
 </div>;
}
