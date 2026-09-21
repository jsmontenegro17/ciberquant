import { codeLabel } from '../../utils/spanish';
import {useState} from 'react';
import {Link,useNavigate,useParams,useSearchParams} from 'react-router-dom';
import {useQuery,useMutation,useQueryClient} from '@tanstack/react-query';
import {validationApi,type ValidationInput,type Metrics,type ValidationRun} from '../../api/validation';
import {marketApi,datasetOnly,type Coverage} from '../../api/marketData';
import {Failure,Paging} from '../market-data/Shared';

export function ValidationWarning(){return <p className="researchWarning">La validación histórica no garantiza rentabilidad futura. La evidencia en vivo y simulada se mantiene separada. OOS significa fuera del tramo de desarrollo de este proceso; CiberQuant no puede garantizar que los datos reservados nunca se hayan consultado externamente. Rendimiento fijo supuesto e importe unitario.</p>;}
function Reuse({run}:{run:ValidationRun}){const w=run.holdout_warnings;return <section aria-label="Historial de investigación"><p>Intentos anteriores: {w.prior_validation_count} · Revelado anteriormente: {w.prior_revealed_holdout_count} · Superposición: {w.overlapping_holdout_count}</p>{w.overlapping_holdout_count>0&&<p className="researchWarning">MUESTRA RESERVADA REUTILIZADA: no es evidencia independiente.</p>}{w.replay_count>0&&<p className="researchWarning">REPRODUCCIÓN: no es evidencia nueva e independiente.</p>}</section>;}
const metricKeys=['trades_executed','wins','losses','draws','resolved_trades','win_rate_percent','break_even_win_rate_percent','edge_percentage_points','ev_per_resolved_trade','total_unit_pnl','max_drawdown_units'];
const metricLabels=["Operaciones","Aciertos","Pérdidas","Empates","Resueltas",'Aciertos %',"Punto de equilibrio %","Ventaja en puntos porcentuales",'EV',"Unidades",'Caída en unidades'];
function MetricsTable({rows}:{rows:{label:string;metrics:Metrics}[]}){return <div className="tableWrap"><table><thead><tr><th>Segmento</th>{metricLabels.map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{rows.map(r=><tr key={r.label}><th>{r.label}</th>{metricKeys.map(k=><td key={k}>{r.metrics[k]??'—'}</td>)}</tr>)}</tbody></table></div>;}

export function ValidationList(){
 const [offset,setOffset]=useState(0);
 const q=useQuery({queryKey:['validations',offset],queryFn:()=>validationApi.list(offset)});
 return <section className="panel"><h2>Validación</h2><ValidationWarning/><p>Crea un plan desde una versión inmutable de una estrategia en estado TESTING (en prueba), en <Link to="/strategies">Estrategias</Link>.</p><Failure error={q.error}/>{q.isPending&&<p>Cargando historial de validación…</p>}{q.data?.total===0&&<p>Todavía no hay planes de validación.</p>}<div className="tableWrap"><table><thead><tr>{['Plan / versión',"Conjunto de datos",'Estado / prueba',"Veredicto","Estado de validación","Creación"].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{q.data?.items.map(r=><tr key={r.id}><td><Link to={`/validation/${r.id}`}>{r.strategy_name?`${r.strategy_name} · `:''}Plan n.º{r.id} / versión n.º{r.version_number??r.strategy_version_id}</Link></td><td>{Object.values(r.dataset).join(' / ')}</td><td>{codeLabel(r.status)} / {r.test_revealed_at?'REVEALED':"Sin revelar"}</td><td>{codeLabel(r.verdict)}</td><td>{codeLabel(r.validation_state)}</td><td>{r.created_at}</td></tr>)}</tbody></table></div>{q.data&&<Paging {...q.data} change={setOffset}/>}</section>;
}

export function ValidationSetup(){
 const [search]=useSearchParams(),navigate=useNavigate();
 const version=Number(search.get('version'));
 const [offset,setOffset]=useState(0),[dataset,setDataset]=useState<Coverage|null>(null);
 const [start,setStart]=useState(''),[end,setEnd]=useState(''),[asOf,setAsOf]=useState(''),[payout,setPayout]=useState('84'),[expiry,setExpiry]=useState(1),[overlap,setOverlap]=useState('ALLOW');
 const coverage=useQuery({queryKey:['coverage',offset],queryFn:()=>marketApi.coverage(offset)});
 const protocol=useQuery({queryKey:['validation-definitions'],queryFn:validationApi.definitions});
 const preview=useMutation({mutationFn:validationApi.preview});
 const create=useMutation({mutationFn:validationApi.create,onSuccess:r=>navigate(`/validation/${r.id}`)});
 function input():ValidationInput{return {strategy_version_id:version,dataset:datasetOnly(dataset!),overall_start:start,overall_end:end,as_of_candle_id:asOf?Number(asOf):null,payout_percent:payout,expiry_bars:expiry,overlap_policy:overlap};}
 const frozen=preview.data?.config_snapshot;
 return <section className="panel formPanel"><h2>Validar versión inmutable n.º{version}</h2><ValidationWarning/><Failure error={coverage.error}/><Failure error={protocol.error}/><Failure error={preview.error}/><Failure error={create.error}/>
 {protocol.data&&<p>{protocol.data.validation_engine_version} · Partición {protocol.data.split.join(' / ')} · {protocol.data.fold_count} particiones · {protocol.data.bootstrap.iterations} iteraciones bootstrap. Mínimo de prueba: {protocol.data.minimum_resolved} resueltas / {protocol.data.minimum_active_days} días UTC activos.</p>}
 <form onChange={()=>preview.reset()} onSubmit={e=>{e.preventDefault();preview.mutate(input());}}>
 <label>Conjunto de datos<select required value={dataset?JSON.stringify(datasetOnly(dataset)):''} onChange={e=>{const d=coverage.data?.items.find(x=>JSON.stringify(datasetOnly(x))===e.target.value)??null;setDataset(d);setStart(d?.first_candle??'');setEnd(d?new Date(Date.parse(d.last_candle)+1).toISOString():'');}}><option value="">Selecciona un conjunto de datos</option>{coverage.data?.items.map(d=><option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{Object.values(datasetOnly(d)).join(' / ')}</option>)}</select></label>
 <label>Inicio global (UTC)<input required value={start} onChange={e=>setStart(e.target.value)}/></label><label>Fin global (UTC)<input required value={end} onChange={e=>setEnd(e.target.value)}/></label>
 <p>Establece el fin global en el cierre de la última vela deseada. Las señales se basan en el cierre; los resultados deben finalizar dentro de su partición.</p>
 <div className="grid compact"><label>ID de vela de corte<input type="number" min="0" value={asOf} onChange={e=>setAsOf(e.target.value)}/></label><label>Rendimiento %<input required value={payout} onChange={e=>setPayout(e.target.value)}/></label><label>Velas hasta vencimiento<input required type="number" min="1" max="60" value={expiry} onChange={e=>setExpiry(Number(e.target.value))}/></label><label>Política de superposición<select value={overlap} onChange={e=>setOverlap(e.target.value)}><option value={"ALLOW"}>{codeLabel("ALLOW")}</option><option value={"SKIP_UNTIL_EXPIRY"}>{codeLabel("SKIP_UNTIL_EXPIRY")}</option></select></label></div>
 <button disabled={!dataset||!version||preview.isPending||create.isPending}>Revisar plan fijo</button></form>
 {coverage.data&&<Paging {...coverage.data} change={n=>{setOffset(n);setDataset(null);preview.reset();}}/>}
 {frozen&&<section aria-label="Vista previa del plan"><h3>Vista previa del plan</h3><p>Datos: {Object.values(frozen.dataset).join(' / ')} · Instantánea de corte: {frozen.as_of_candle_id}</p><p>{frozen.overall_start} → {frozen.overall_end}</p><p>Rendimiento {frozen.payout_percent}% · Vencimiento {frozen.expiry_bars} · {frozen.overlap_policy}</p><ul>{frozen.boundaries.map(b=><li key={b.segment_type+b.fold_number}>{b.segment_type} {b.fold_number||''}: {b.signal_start} → {b.signal_end}</li>)}</ul><p>Crear esta validación fija la versión de estrategia, la instantánea de datos y los límites de las particiones.</p><button disabled={create.isPending} onClick={()=>{const {strategy_version_id,dataset,overall_start,overall_end,as_of_candle_id,payout_percent,expiry_bars,overlap_policy}=frozen;create.mutate({strategy_version_id,dataset,overall_start,overall_end,as_of_candle_id,payout_percent,expiry_bars,overlap_policy});}}>{create.isPending?"Calculando desarrollo…":"Crear plan de validación"}</button></section>}
 </section>;
}

export function ValidationDetail(){
 const id=Number(useParams().id),cache=useQueryClient(),[confirm,setConfirm]=useState(false);
 const q=useQuery({queryKey:['validation',id],queryFn:()=>validationApi.detail(id),refetchInterval:q=>q.state.data?.status.startsWith('RUNNING')?3000:false});
 const segments=useQuery({queryKey:['validation-segments',id,q.data?.status],queryFn:()=>validationApi.segments(id)});
 const reveal=useMutation({mutationFn:()=>validationApi.reveal(id),onSuccess:r=>{cache.setQueryData(['validation',id],r);cache.invalidateQueries({queryKey:['versions']});cache.invalidateQueries({queryKey:['validations']});setConfirm(false);}});
 const r=q.data;
 return <section className="panel"><h2>Evidencia de validación n.º{id}</h2><ValidationWarning/><Failure error={q.error}/><Failure error={segments.error}/><Failure error={reveal.error}/>{q.isPending&&<p>Cargando evidencia…</p>}{r&&<>
 <p>{r.validation_engine_version} · {codeLabel(r.status)} · {codeLabel(r.validation_state)} · Último intento: {r.latest_validation_attempt}</p><p>Huella de configuración: {r.config_sha256}</p><p>Huella de definición: {r.config_snapshot.definition_sha256}</p><p>Versión n.º{r.strategy_version_id} · {Object.values(r.dataset).join(' / ')} · Corte {r.as_of_candle_id} · {r.overall_start} → {r.overall_end}</p><p>Supuesto de rendimiento fijo: {r.payout_percent}% · Vencimiento {r.expiry_bars} · {r.overlap_policy}</p><Reuse run={r}/>{r.error_summary&&<p role="alert">{r.error_summary}</p>}
 <h3>EVIDENCIA PRELIMINAR</h3>{r.development_summary&&<MetricsTable rows={Object.entries(r.development_summary).map(([label,metrics])=>({label,metrics}))}/>}
 <h3>Evaluación progresiva de una estrategia fija</h3><p>Sin reentrenamiento, optimización ni búsqueda de umbrales. El contexto crece desde el origen canónico.</p>
 {r.walk_forward_summary?.map(f=><section key={f.fold_number}><h4>Partición {f.fold_number} · {f.evaluable?"Evaluable":"Insuficiente"}</h4><p>{r.config_snapshot.boundaries.find(b=>b.fold_number===f.fold_number)?.signal_start} → {r.config_snapshot.boundaries.find(b=>b.fold_number===f.fold_number)?.signal_end}</p><MetricsTable rows={[{label:`Partición ${f.fold_number}`,metrics:Object.fromEntries(Object.entries(f).filter(([,v])=>typeof v!=='boolean')) as Metrics}]}/></section>)}
 <section aria-label="Prueba final"><h3>PRUEBA FINAL — {r.test_revealed_at?'REVEALED':r.status==='SEALED'?'SEALED':'NOT REVEALED'}</h3><p>{r.config_snapshot.boundaries.find(b=>b.segment_type==='TEST')?.signal_start} → {r.config_snapshot.boundaries.find(b=>b.segment_type==='TEST')?.signal_end}</p>
 {!r.test_revealed_at&&<p>Sin calcular. No existen operaciones de prueba, métricas ni bootstrap.</p>}
 {r.status==='SEALED'&&!confirm&&<button onClick={()=>setConfirm(true)}>Revelar prueba final</button>}
 {confirm&&<section role="dialog" aria-label="Confirmar revelación"><p>Una vez revelada, esta muestra reservada deja de considerarse no observada dentro de este proceso de validación.</p><button disabled={reveal.isPending} onClick={()=>reveal.mutate()}>Confirmar revelación irreversible</button><button disabled={reveal.isPending} onClick={()=>setConfirm(false)}>Cancelar</button></section>}
 {r.test_summary&&<MetricsTable rows={[{label:'FINAL TEST',metrics:r.test_summary}]}/>}
 {r.bootstrap_summary&&<section aria-label="Evidencia bootstrap"><h4>Intervalo bootstrap del 95% por bloques de días UTC</h4><p>Resultado neto medio en unidades: {r.bootstrap_summary.point_estimate??'—'} · [{r.bootstrap_summary.lower_95??'—'}, {r.bootstrap_summary.upper_95??'—'}]</p><p>Bloques de días UTC: {r.bootstrap_summary.block_count} · Iteraciones: {r.bootstrap_summary.iterations}</p><p>Semilla: {r.bootstrap_summary.seed}</p><p>Conserva la dependencia intradía; no demuestra independencia entre días ni probabilidad de ganancias futuras.</p></section>}
 </section><h3>{r.verdict==='PASS'?"Validación histórica aprobada (PASS)":r.verdict}</h3>{r.gates&&<ul>{Object.entries(r.gates).map(([gate,pass])=><li key={gate}>{pass?'✓':r.verdict==='INCONCLUSIVE'&&['test_resolved','test_days','evaluable_folds'].includes(gate)?'insufficient':'✗'} {gate}</li>)}</ul>}
 {r.temporal_stability&&Object.entries(r.temporal_stability).map(([kind,months])=><section key={kind}><h3>{kind} · Estabilidad mensual descriptiva UTC</h3><p>Los resultados mensuales son descriptivos, no condiciones adicionales de aprobación.</p><MonthlyChart months={months}/><MetricsTable rows={months.map(m=>({label:m.month,metrics:m}))}/></section>)}
 <h3>Evidencia derivada inmutable</h3><ul>{segments.data?.map(s=><li key={s.id}>{s.segment_type} {s.fold_number||''}: {s.backtest_run_id?<Link to={`/backtests/${s.backtest_run_id}`}>Inspeccionar ejecución derivada n.º{s.backtest_run_id}</Link>:"Sin calcular"}</li>)}</ul>
 </>}</section>;
}

function MonthlyChart({months}:{months:(Metrics&{month:string})[]}){
 const values=months.map(m=>Number(m.total_unit_pnl)),extent=Math.max(1,...values.map(Math.abs));
 return <svg role="img" aria-label="Resultado neto mensual en unidades (descriptivo)" viewBox={`0 0 600 ${Math.max(40,months.length*32)}`} style={{width:'100%',maxHeight:300}}>{months.map((m,i)=><g key={m.month}><text x="0" y={i*32+20} fill="currentColor" fontSize="12">{m.month}</text><line x1="330" y1={i*32} x2="330" y2={i*32+28} stroke="gray"/><rect x={values[i]<0?330+values[i]/extent*220:330} y={i*32+4} width={Math.abs(values[i])/extent*220} height="20" fill="#739db8"/></g>)}</svg>;
}
