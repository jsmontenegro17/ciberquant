import { codeLabel, datasetLabels, evidenceText } from '../../utils/spanish';
import {useEffect,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {scannerApi,type WatchItem} from '../../api/scanner';
import {researchApi} from '../../api/research';
import {marketApi,datasetOnly,type Dataset} from '../../api/marketData';
import {Failure,Paging} from '../market-data/Shared';
import {ProviderPolicy} from './ProviderPolicy';

function Json({value}:{value:unknown}){return <pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(value,null,2)}</pre>;}
export function ScannerCard({item,onToggle}:{item:WatchItem;onToggle:()=>void}){
 const e=item.latest;
 return <section className="panel" aria-label={`Seguimiento ${item.id}`}>
 <h3>{item.dataset.symbol} · {item.dataset.timeframe}</h3><p>{Object.values(item.dataset).join(' / ')}</p>
 <ProviderPolicy provider={item.provider} error={e?.error}/>
 <p>{item.provider==='REPLAY'?'MODO REPRODUCCIÓN':item.provider} · {codeLabel(item.state)} · {item.research_mode?'INVESTIGACIÓN: sin validar para seguimiento normal':"Seguimiento validado"}</p>
 {item.provider==='IQOPTION'&&<p className="researchWarning">INTEGRACIÓN COMUNITARIA NO OFICIAL: el protocolo puede cambiar sin aviso. PRACTICE / solo lectura. Producto: {e?.payout_product??"Sin verificar"}. El rendimiento observado no garantiza una cotización ejecutable.</p>}
 <h4>{e?.strategy_name??`Versión n.º${item.strategy_version_id}`} {e?.version?`v${e.version}`:''} · {e?.state==='MATCH'?'CONDICIONES CUMPLIDAS':e?.state??"Esperando velas cerradas"}</h4>
 <p>Dirección de investigación: {e?.research_direction??'—'} · Señal de investigación: no se envió ninguna orden.</p>
 <p>Validación: {e?.validation_state??"Comprobando"} · Datos: {e?.dataset_validation_state??"Comprobando"}</p>
 <p>Rendimiento actual del proveedor: {e?.current_payout!=null?`${e.current_payout}%`:"No disponible"} · Punto de equilibrio %: {e?.current_break_even??"No disponible"}</p>
 <p>Rendimiento de la validación histórica: {e?.validation_payout!=null?`${e.validation_payout}%`:"No disponible"} · Vencimiento de validación histórica: {e?.validation_expiry??"No disponible"} velas{item.research_mode?' — solo referencia, no configuración de la simulación de investigación.':'.'}</p>
 {item.research_mode&&<>
 <p>Supuesto de vencimiento de investigación: {item.research_expiry??"No disponible"} velas</p>
 {e?.current_payout!=null?<p>Supuesto alternativo de investigación: {item.research_payout??"No disponible"}% — no se usa mientras esté disponible el rendimiento del proveedor.</p>:<p>Supuesto de rendimiento de investigación: {item.research_payout??"No disponible"}%</p>}
 </>}
 {e?.payout_source&&<p>Rendimiento fijado de la simulación: {e.payout_snapshot??"No disponible"}% · {e.payout_source}. Vencimiento simulado: {e.expiry_bars??"No disponible"} velas · {e.expiry_source??"No disponible"}.</p>}
 {e?.payout_warning&&<p role="alert" className="researchWarning">RENDIMIENTO INFERIOR AL SUPUESTO DE VALIDACIÓN</p>}
 {item.state==='SUSPENDED_DEGRADED'&&<p role="alert">DEGRADADO: seguimiento normal suspendido.</p>}
 <p>Señal disponible: {e?.signal_time??'—'} · Límite de apertura de la siguiente vela: {e?.next_entry_boundary??'—'}. El precio de entrada futuro se desconoce.</p>
 <p>Vela de señal: {e?.signal_open??'—'} → {e?.signal_time??'—'} · Latencia de recepción en ms: {e?.latency_ms??'No disponible / reproducción lógica'}. La detección no es una cotización ejecutable.</p>
 {e?.error&&<p role="alert">{e.error}</p>}
 <details><summary>Estado del proveedor y contexto exacto de la señal</summary><Json value={e?.health}/><Json value={e?.signal_context}/><Json value={e?.features}/></details>
 <button onClick={onToggle}>{item.enabled?"Pausar seguimiento":"Activar seguimiento"}</button>
 </section>;
}

function Snapshot({id}:{id:number}){
 const q=useQuery({queryKey:['scanner','snapshot',id],queryFn:()=>scannerApi.snapshot(id),refetchInterval:2000});
 return <section className="panel"><h3>Instantánea en vivo · seguimiento n.º{id}</h3><Failure error={q.error}/><p>La vela en formación es provisional, nunca una señal definitiva. El estado pierde vigencia si se detiene el proceso de seguimiento.</p><Json value={q.data?.subscription}/></section>;
}

export function Scanner(){
 const cache=useQueryClient(),[research,setResearch]=useState(false),[offset,setOffset]=useState(0),[eventOffset,setEventOffset]=useState(0);
 const [name,setName]=useState(''),[list,setList]=useState(0),[provider,setProvider]=useState('REPLAY'),[strategy,setStrategy]=useState(0),[version,setVersion]=useState(0),[strategyOffset,setStrategyOffset]=useState(0),[versionOffset,setVersionOffset]=useState(0),[coverageOffset,setCoverageOffset]=useState(0);
 const [dataset,setDataset]=useState<Dataset>({source:'',broker:'',symbol:'',market_type:'REGULAR',timeframe:'1m'});
 const [payout,setPayout]=useState('84'),[expiry,setExpiry]=useState(1),[selected,setSelected]=useState(0);
 const providers=useQuery({queryKey:['providers'],queryFn:scannerApi.providers,refetchInterval:5000});
 const lists=useQuery({queryKey:['scanner','lists'],queryFn:scannerApi.lists});
 const items=useQuery({queryKey:['scanner','items',research,offset],queryFn:()=>scannerApi.items(research,offset),refetchInterval:2000});
 const events=useQuery({queryKey:['scanner','events',eventOffset],queryFn:()=>scannerApi.events(eventOffset),refetchInterval:2000});
 const coverage=useQuery({queryKey:['coverage',coverageOffset],queryFn:()=>marketApi.coverage(coverageOffset)});
 const strategies=useQuery({queryKey:['strategies',strategyOffset],queryFn:()=>researchApi.strategies(strategyOffset)});
 const versions=useQuery({queryKey:['versions',strategy,versionOffset],queryFn:()=>researchApi.versions(strategy,versionOffset),enabled:!!strategy});
 const refresh=()=>cache.invalidateQueries({queryKey:['scanner']});
 const createList=useMutation({mutationFn:scannerApi.createList,onSuccess:r=>{setList(r.id);setName('');refresh();}});
 const createItem=useMutation({mutationFn:scannerApi.createItem,onSuccess:()=>refresh()});
 const toggle=useMutation({mutationFn:scannerApi.toggle,onSuccess:()=>refresh()});
 useEffect(()=>{
  if(typeof EventSource==='undefined')return;
  const stream=new EventSource(`${import.meta.env.VITE_API_BASE_URL||'http://localhost:8000/api/v1'}/scanner/stream`,{withCredentials:true});
  stream.onmessage=()=>{void cache.invalidateQueries({queryKey:['scanner']});};
  return ()=>stream.close();
 },[cache]);
 return <>
 <section className="panel"><h2>Seguimiento de estrategias en vivo</h2><p className="researchWarning">Señal de investigación: no se envían órdenes. No se crean operaciones, sesiones, saldos ni movimientos. La validación histórica no es una garantía. Las observaciones simuladas no son pruebas históricas.</p>
 <h3>Proveedores</h3>{providers.data?.items.map(p=><details key={p.provider}><summary>{p.provider} · {p.enabled?"Habilitado":"Deshabilitado"} · {codeLabel(p.mode)}</summary><p>{evidenceText(p.warning)}</p><Json value={p.capabilities}/></details>)}
 {[providers,lists,items,events,coverage,strategies,versions,createList,createItem,toggle].map((q,i)=><Failure key={i} error={q.error}/>)}
 <label><input type="checkbox" checked={research} onChange={e=>{setResearch(e.target.checked);setOffset(0);}}/>Incluir seguimientos de investigación (modo explícitamente no validado)</label>
 </section>
 <section className="panel formPanel"><h3>Configuración de seguimiento</h3>
 <form onSubmit={e=>{e.preventDefault();createList.mutate(name);}}><label>Nombre de la lista<input required maxLength={120} value={name} onChange={e=>setName(e.target.value)}/></label><button disabled={createList.isPending}>Crear lista de seguimiento</button></form>
 <form onSubmit={e=>{e.preventDefault();createItem.mutate({list,body:{provider,dataset,strategy_version_id:version,research_mode:research,...(research?{research_payout:payout,research_expiry:expiry}:{})}});}}>
 <label>Lista de seguimiento<select required value={list||''} onChange={e=>setList(Number(e.target.value))}><option value="">Selecciona una lista de seguimiento</option>{lists.data?.items.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
 <label>Proveedor<select value={provider} onChange={e=>setProvider(e.target.value)}>{['REPLAY','MT5','IQOPTION'].map(p=><option key={p} value={p}>{codeLabel(p)}</option>)}</select></label>
 <label>Datos existentes<select value="" onChange={e=>setDataset(JSON.parse(e.target.value))}><option value="">Selecciona datos o introduce su identidad completa debajo</option>{coverage.data?.items.map(d=><option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{Object.values(datasetOnly(d)).join(' / ')}</option>)}</select></label>
 {coverage.data&&<Paging {...coverage.data} change={setCoverageOffset}/>}
 <div className="grid compact">{(['source','broker','symbol'] as const).map(k=><label key={k}>{datasetLabels[k]}<input required value={dataset[k]} onChange={e=>setDataset({...dataset,[k]:e.target.value})}/></label>)}<label>Tipo de mercado<select value={dataset.market_type} onChange={e=>setDataset({...dataset,market_type:e.target.value})}><option value={"REGULAR"}>{codeLabel("REGULAR")}</option><option value={"OTC"}>{codeLabel("OTC")}</option></select></label><label>Temporalidad<select value={dataset.timeframe} onChange={e=>setDataset({...dataset,timeframe:e.target.value})}>{['1m','5m','15m','30m','1h'].map(t=><option key={t} value={t}>{codeLabel(t)}</option>)}</select></label></div>
 <label>Estrategia<select required value={strategy||''} onChange={e=>{setStrategy(Number(e.target.value));setVersion(0);setVersionOffset(0);}}><option value="">Selecciona una estrategia</option>{strategies.data?.items.map(s=><option key={s.id} value={s.id}>{s.name} · {codeLabel(s.status)}</option>)}</select></label>{strategies.data&&<Paging {...strategies.data} change={setStrategyOffset}/>}
 <label>Versión inmutable<select required value={version||''} onChange={e=>setVersion(Number(e.target.value))}><option value="">Selecciona una versión</option>{versions.data?.items.map(v=><option key={v.id} value={v.id}>v{v.version} · {v.validation_state??'NOT_VALIDATED'}</option>)}</select></label>{versions.data&&<Paging {...versions.data} change={setVersionOffset}/>}
 <p>El seguimiento normal requiere estado TESTING (en prueba) y validación histórica PASS para la misma fuente, bróker, símbolo, mercado y temporalidad. El servidor comprueba la compatibilidad; una aprobación general no basta.</p>
 {research&&<div className="grid compact"><label>Rendimiento supuesto de simulación %<input required value={payout} onChange={e=>setPayout(e.target.value)}/></label><label>Velas de vencimiento de investigación<input type="number" min={1} max={60} value={expiry} onChange={e=>setExpiry(Number(e.target.value))}/></label></div>}
 <button disabled={!list||!version||createItem.isPending}>Crear seguimiento e iniciar proveedor</button></form></section>
 <section aria-label="Conjuntos de datos en seguimiento"><h2>Conjuntos de datos en seguimiento</h2>{items.data?.total===0&&<p>No hay seguimientos para este filtro.</p>}{items.data?.items.map(item=><div key={item.id}><ScannerCard item={item} onToggle={()=>toggle.mutate({id:item.id,enabled:!item.enabled})}/><button onClick={()=>setSelected(item.id)}>Inspeccionar instantánea n.º{item.id}</button></div>)}{items.data&&<Paging {...items.data} change={setOffset}/>}</section>
 {selected>0&&<Snapshot id={selected}/>}
 <section className="panel"><h2>Historial de eventos</h2><div className="tableWrap"><table><thead><tr>{['Hora / modo',"Conjunto de datos",'Estrategia / dirección',"Estado",'Rendimiento / validación',"Observación simulada"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{events.data?.items.map(e=><tr key={e.id}><td>{e.signal_time}<br/>{e.mode==='REPLAY'?'MODO REPRODUCCIÓN':e.mode}</td><td>{Object.values(e.dataset).join(' / ')}</td><td>#{e.strategy_version_id} · {codeLabel(e.direction)}</td><td>{codeLabel(e.state)}</td><td>{e.current_payout??"No disponible"} / {e.validation_state_snapshot}</td><td>{e.paper_outcome?<details><summary>{e.mode==='REPLAY'?'OBSERVACIÓN SIMULADA EN REPRODUCCIÓN':'OBSERVACIÓN SIMULADA EN VIVO'} · {codeLabel(e.paper_outcome.result)}</summary><Json value={e.paper_outcome.evidence}/></details>:e.state==='MATCH'?"Pendiente de futuras velas observadas":'—'}</td></tr>)}</tbody></table></div>{events.data&&<Paging {...events.data} change={setEventOffset}/>}</section>
 </>;
}
