import { codeLabel, evidenceText } from '../../utils/spanish';
import {useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {api} from '../../api/client';
import {marketApi,datasetOnly,params,type Dataset,type Page} from '../../api/marketData';
import {researchApi} from '../../api/research';
import {Failure,Paging} from '../market-data/Shared';
import {ProviderPolicy} from '../scanner/ProviderPolicy';

type Stage={name:string;status:string;href:string;date:string|null;evidence:unknown;summary?:string};
export type Overview={dataset:Dataset;version:{id:number};pipeline:Stage[];provider_health:{provider:string;health?:{error?:string}}[];
 evidence:{manual:{id:number;href:string}|null;validation:{id:number;href:string}|null};comparison_note:string};
type EventRow={id:number;state:string;mode:string;signal_time:string;href:string};
function Evidence({value}:{value:unknown}){return <pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(value,null,2)}</pre>;}
export function Pipeline({data}:{data:Overview}){
 return <><p>{Object.values(data.dataset).join(' / ')} · Versión de estrategia n.º{data.version.id}</p>
 <ol className="grid compact" aria-label="Etapas de investigación">{data.pipeline.map(s=><li key={s.name}><Link to={s.href}>{codeLabel(s.name)}</Link><p>{codeLabel(s.status)}</p><p>{evidenceText(s.summary)}</p><small>{s.date?`${new Date(s.date).toLocaleString('es-CO',{timeZone:'UTC'})} UTC`:"Sin fecha de evidencia"}</small><details><summary>{s.name} evidencia</summary><Evidence value={s.evidence}/></details></li>)}</ol>
 <p className="researchWarning">{evidenceText(data.comparison_note)}</p></>;
}
export function Context({dataset,version}:{dataset:Dataset;version:number}){
 const [offset,setOffset]=useState(0),[historyOffset,setHistoryOffset]=useState(0),[kind,setKind]=useState('manual');
 const query=params({...dataset,strategy_version_id:version});
 const q=useQuery({queryKey:['workspace',query],queryFn:()=>api<Overview>(`/workspace/overview?${query}`),refetchInterval:5000});
 const events=useQuery({queryKey:['workspace-events',query,offset],queryFn:()=>api<Page<EventRow>>(`/workspace/events?${query}&offset=${offset}`)});
 const [paperOffset,setPaperOffset]=useState(0);
 const paper=useQuery({queryKey:['workspace-paper',query,paperOffset],queryFn:()=>api<Page<Record<string,unknown>>>(`/workspace/paper?${query}&offset=${paperOffset}`)});
 const ops=useQuery({queryKey:['operations'],queryFn:()=>api('/operations/status'),refetchInterval:5000});
 const history=useQuery({queryKey:['workspace-history',query,kind,historyOffset],queryFn:()=>api<Page<{id:number;href:string;status:string}>>(`/workspace/history?${query}&kind=${kind}&offset=${historyOffset}`)});
 const a=q.data?.evidence.manual?.id,b=q.data?.evidence.validation?.id;
 const comparison=useQuery({queryKey:['workspace-compare',query,a,b],queryFn:()=>api<{status:string;differences:string[]}>(`/workspace/comparison?${query}&backtest_id=${a}&validation_id=${b}`),enabled:!!a&&!!b});
 return <>{[q,events,history,comparison,paper,ops].map((x,i)=><Failure key={i} error={x.error}/>)}{q.isPending&&<p>Cargando evidencia de investigación…</p>}
 {q.data&&<><Pipeline data={q.data}/><h3>Histórico frente a simulación en vivo</h3><p>Última prueba histórica manual: {a?<Link to={`/backtests/${a}`}>#{a}</Link>:'MISSING'} · Última validación histórica: {b?<Link to={`/validation/${b}`}>#{b}</Link>:'MISSING'}</p>
 {comparison.data?<details><summary>Comparación · {codeLabel(comparison.data.status)}</summary><Evidence value={comparison.data}/></details>:<p>La comparación estará disponible cuando existan ambas fuentes.</p>}
 <h3>Estado del proveedor</h3>{q.data.provider_health.map((h,i)=><ProviderPolicy key={i} provider={h.provider} error={h.health?.error}/>)}{q.data.provider_health.length?<details><summary>Inspeccionar estado actual del seguimiento ({q.data.provider_health.length})</summary><Evidence value={q.data.provider_health}/></details>:<p>No hay seguimiento del proveedor para este contexto exacto.</p>}</>}
 <h3>Historial de evidencia</h3><label>Fuente del historial<select value={kind} onChange={e=>{setKind(e.target.value);setHistoryOffset(0);}}><option value="manual">Pruebas históricas manuales</option><option value="validation">Validación histórica</option></select></label>
 {history.data?.items.map(r=><p key={r.id}><Link to={r.href}>#{r.id} · {codeLabel(r.status)}</Link></p>)}{history.data&&<Paging {...history.data} change={setHistoryOffset}/>}
 <h3>Evidencia reciente de seguimiento y simulación</h3>{events.data?.total===0&&<p>No hay eventos de seguimiento para este contexto exacto.</p>}
 <details><summary>Simulaciones por modo, rendimiento, vencimiento y resultado</summary><p>Los contratos distintos no se combinan. GAP/UNAVAILABLE (hueco/no disponible) no son pérdidas.</p><Evidence value={paper.data?.items}/>{paper.data&&<Paging {...paper.data} change={setPaperOffset}/>}</details>
 <details><summary>Diagnóstico operativo y estado de recuperación</summary><Evidence value={ops.data}/></details>
 {events.data?.items.map(e=><p key={e.id}><Link to={e.href}>Evento n.º{e.id} · {codeLabel(e.state)} · {codeLabel(e.mode)} · {e.signal_time}</Link></p>)}{events.data&&<Paging {...events.data} change={setOffset}/>}
 <h3>Evidencia de sesiones manuales y diario</h3><p>Evidencia de cuentas separada. No se asocia automáticamente con esta estrategia ni con resultados simulados.</p><Link to="/journal">Consultar diario</Link> · <Link to="/sessions">Consultar sesiones</Link></>;
}
export default function Workspace(){
 const [dataset,setDataset]=useState<Dataset|null>(null),[strategy,setStrategy]=useState(0),[version,setVersion]=useState(0);
 const [dataOffset,setDataOffset]=useState(0),[strategyOffset,setStrategyOffset]=useState(0),[versionOffset,setVersionOffset]=useState(0);
 const datasets=useQuery({queryKey:['coverage',dataOffset],queryFn:()=>marketApi.coverage(dataOffset)});
 const strategies=useQuery({queryKey:['strategies',strategyOffset],queryFn:()=>researchApi.strategies(strategyOffset)});
 const versions=useQuery({queryKey:['versions',strategy,versionOffset],queryFn:()=>researchApi.versions(strategy,versionOffset),enabled:!!strategy});
 return <section className="panel"><h2>Área de investigación</h2><p>Consulta evidencia, no recomendaciones para operar. Selecciona datos exactos y una versión inmutable.</p>
 {[datasets,strategies,versions].map((q,i)=><Failure key={i} error={q.error}/>)}
 <label>Conjunto de datos<select aria-label="Datos del área de investigación" value={dataset?JSON.stringify(dataset):''} onChange={e=>setDataset(e.target.value?JSON.parse(e.target.value):null)}><option value="">Elige un conjunto de datos exacto</option>{datasets.data?.items.map(d=><option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{Object.values(datasetOnly(d)).join(' / ')}</option>)}</select></label>
 {datasets.isPending&&<p>Cargando conjuntos de datos…</p>}{datasets.data?.total===0&&<p>No hay conjuntos de datos. <Link to="/market-data">Importar datos de mercado</Link></p>}{datasets.data&&<Paging {...datasets.data} change={setDataOffset}/>}
 <label>Estrategia<select aria-label="Estrategia del área de investigación" value={strategy} onChange={e=>{setStrategy(Number(e.target.value));setVersion(0);setVersionOffset(0);}}><option value={0}>Elige una estrategia</option>{strategies.data?.items.map(s=><option key={s.id} value={s.id}>{s.name} · #{s.id}</option>)}</select></label>{strategies.data&&<Paging {...strategies.data} change={setStrategyOffset}/>}
 <label>Versión de estrategia<select aria-label="Versión del área de investigación" value={version} onChange={e=>setVersion(Number(e.target.value))}><option value={0}>Elige una versión inmutable</option>{versions.data?.items.map(v=><option key={v.id} value={v.id}>v{v.version} · #{v.id}</option>)}</select></label>{versions.data&&<Paging {...versions.data} change={setVersionOffset}/>}
 {dataset&&version?<Context key={JSON.stringify(dataset)+version} dataset={dataset} version={version}/>:<p>No has elegido un contexto. No se seleccionan estrategias ni datos automáticamente.</p>}</section>;
}
export function WorkspaceEvent(){
 const id=Number(useParams().id);
 const q=useQuery({queryKey:['workspace-event',id],queryFn:()=>api(`/workspace/events/${id}`)});
 return <section className="panel"><h2>Trazabilidad de seguimiento y simulación n.º{id}</h2><p>Observación simulada en vivo o reproducción identificada como REPLAY; no es una operación en el bróker.</p><Failure error={q.error}/>{q.isPending?<p>Cargando evidencia…</p>:<Evidence value={q.data}/>}<Link to="/workspace">Área de investigación</Link> · <Link to="/scanner">Abrir seguimiento</Link></section>;
}
