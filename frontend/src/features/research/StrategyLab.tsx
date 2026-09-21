import { codeLabel } from '../../utils/spanish';
import {useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {useQuery,useMutation,useQueryClient} from '@tanstack/react-query';
import {researchApi,type Version} from '../../api/research';
import {Failure,Paging} from '../market-data/Shared';
import {VersionBuilder} from './VersionBuilder';
import {RunSetup} from './RunSetup';
export function ResearchWarning(){return <p className="researchWarning">DENTRO DE LA MUESTRA · SIN VALIDAR. Investigación histórica bajo supuestos; no garantiza resultados futuros.</p>;}
export function StrategyLab(){
  const [offset,setOffset]=useState(0),[name,setName]=useState(''),[description,setDescription]=useState('');
  const cache=useQueryClient();
  const list=useQuery({queryKey:['strategies',offset],queryFn:()=>researchApi.strategies(offset)});
  const create=useMutation({mutationFn:()=>researchApi.create(name,description),onSuccess:()=>{setName('');setDescription('');cache.invalidateQueries({queryKey:['strategies']});}});
  return <><section className="panel formPanel"><h2>Estrategias</h2><ResearchWarning/><Failure error={list.error}/><Failure error={create.error}/>
    <form onSubmit={e=>{e.preventDefault();create.mutate();}}><label>Nombre<input required maxLength={120} value={name} onChange={e=>setName(e.target.value)}/></label><label>Descripción<textarea maxLength={2000} value={description} onChange={e=>setDescription(e.target.value)}/></label><button disabled={create.isPending}>Crear estrategia</button></form>
    {create.data && <p>Creada: <Link to={`/strategies/${create.data.id}`}>{create.data.name}</Link></p>}
    {list.isPending&&<p>Cargando estrategias…</p>}{list.data?.total===0&&<p>Todavía no has creado estrategias.</p>}
    <div className="tableWrap"><table><thead><tr>{["Nombre","Estado","Última versión","Dirección","Motor de indicadores","Última prueba histórica manual"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{list.data?.items.map(s=><tr key={s.id}><td><Link to={`/strategies/${s.id}`}>{s.name}</Link></td><td>{codeLabel(s.status)}</td><td>{s.latest_version?`v${s.latest_version.version}`:'—'}</td><td>{s.latest_version?.trade_direction??'—'}</td><td>{s.latest_version?.feature_engine_version??'—'}</td><td>{s.last_backtest?<Link to={`/backtests/${s.last_backtest.id}`}>#{s.last_backtest.id} {codeLabel(s.last_backtest.status)}</Link>:'—'}</td></tr>)}</tbody></table></div>
    {list.data&&<Paging {...list.data} change={setOffset}/>}</section></>;
}
export function StrategyDetail(){
  const id=Number(useParams().id),cache=useQueryClient();
  const [offset,setOffset]=useState(0),[copy,setCopy]=useState<Version|undefined>(),[selected,setSelected]=useState<Version|null>(null),[revision,setRevision]=useState(0);
  const strategy=useQuery({queryKey:['strategy',id],queryFn:()=>researchApi.strategy(id)});
  const versions=useQuery({queryKey:['versions',id,offset],queryFn:()=>researchApi.versions(id,offset)});
  const definitions=useQuery({queryKey:['strategy-definitions'],queryFn:researchApi.definitions});
  const status=useMutation({mutationFn:(value:string)=>researchApi.status(id,value),onSuccess:()=>{cache.invalidateQueries({queryKey:['strategy',id]});cache.invalidateQueries({queryKey:['strategies']});}});
  return <><section className="panel"><h2>{strategy.data?.name??"Estrategia"}</h2><ResearchWarning/><Failure error={strategy.error}/><Failure error={versions.error}/><Failure error={status.error}/>
    {strategy.data&&<><p>{strategy.data.description}</p><label>Estado<select value={strategy.data.status} disabled={status.isPending} onChange={e=>status.mutate(e.target.value)}>{definitions.data?.statuses.map(s=><option key={s} value={s}>{codeLabel(s)}</option>)}</select></label></>}
    <h3>Historial de versiones inmutables</h3>{versions.data?.items.map(v=><article className="panel" key={v.id}><h3>v{v.version} · {codeLabel(v.trade_direction)}</h3><p>{v.created_at} UTC · {v.feature_engine_version}</p><p>Huella de definición: {v.definition_sha256}</p><details><summary>Definición</summary><pre>{JSON.stringify(v.condition_tree,null,2)}</pre></details><div className="actions"><button disabled={strategy.data?.status==='DISABLED'} onClick={()=>setSelected(v)}>Probar históricamente v{v.version}</button><button className="secondary" disabled={'conditions' in v.condition_tree && v.condition_tree.conditions.some(c=>'conditions' in c)} onClick={()=>{setCopy(v);setRevision(revision+1);}}>Copiar v{v.version} a una nueva versión</button></div></article>)}
    {versions.data?.items.map(v=><p key={`validation-${v.id}`}>v{v.version}: {v.validation_state??'NOT_VALIDATED'} · Último intento: {v.latest_validation_attempt??"Ninguno"} {strategy.data?.status==='TESTING'&&<Link to={`/validation/new?version=${v.id}`}>Validar v{v.version}</Link>}</p>)}
    {versions.data&&<Paging {...versions.data} change={setOffset}/>}</section>
    {strategy.data&&<VersionBuilder key={`${id}-${revision}`} strategyId={id} copy={copy} onSaved={()=>{cache.invalidateQueries({queryKey:['versions',id]});cache.invalidateQueries({queryKey:['strategies']});setOffset(0);}}/>}
    {selected&&<RunSetup key={selected.id} version={selected}/>}</>;
}
