import {useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {api} from '../../api/client';
import {marketApi,datasetOnly,params,type Dataset,type Page} from '../../api/marketData';
import {researchApi} from '../../api/research';
import {Failure,Paging} from '../market-data/Shared';

type Stage={name:string;status:string;href:string;date:string|null;evidence:unknown;summary?:string};
export type Overview={dataset:Dataset;version:{id:number};pipeline:Stage[];provider_health:unknown[];
 evidence:{manual:{id:number;href:string}|null;validation:{id:number;href:string}|null};comparison_note:string};
type EventRow={id:number;state:string;mode:string;signal_time:string;href:string};
function Evidence({value}:{value:unknown}){return <pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(value,null,2)}</pre>;}
export function Pipeline({data}:{data:Overview}){
 return <><p>{Object.values(data.dataset).join(' / ')} · StrategyVersion #{data.version.id}</p>
 <ol className="grid compact" aria-label="Research pipeline">{data.pipeline.map(s=><li key={s.name}><Link to={s.href}>{s.name}</Link><p>{s.status}</p><p>{s.summary}</p><small>{s.date?`${new Date(s.date).toLocaleString('en-GB',{timeZone:'UTC'})} UTC`:'No evidence timestamp'}</small><details><summary>{s.name} evidence</summary><Evidence value={s.evidence}/></details></li>)}</ol>
 <p className="researchWarning">{data.comparison_note}</p></>;
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
 return <>{[q,events,history,comparison,paper,ops].map((x,i)=><Failure key={i} error={x.error}/>)}{q.isPending&&<p>Loading research evidence…</p>}
 {q.data&&<><Pipeline data={q.data}/><h3>Historical vs live paper</h3><p>Last manual backtest: {a?<Link to={`/backtests/${a}`}>#{a}</Link>:'MISSING'} · Latest historical validation: {b?<Link to={`/validation/${b}`}>#{b}</Link>:'MISSING'}</p>
 {comparison.data?<details><summary>Comparison · {comparison.data.status}</summary><Evidence value={comparison.data}/></details>:<p>Comparison unavailable until both sources exist.</p>}
 <h3>Provider health</h3>{q.data.provider_health.length?<details><summary>Inspect current subscription health ({q.data.provider_health.length})</summary><Evidence value={q.data.provider_health}/></details>:<p>No provider subscription for this exact context.</p>}</>}
 <h3>Evidence history</h3><label>History source<select value={kind} onChange={e=>{setKind(e.target.value);setHistoryOffset(0);}}><option value="manual">Manual backtests</option><option value="validation">Historical validation</option></select></label>
 {history.data?.items.map(r=><p key={r.id}><Link to={r.href}>#{r.id} · {r.status}</Link></p>)}{history.data&&<Paging {...history.data} change={setHistoryOffset}/>}
 <h3>Recent scanner / paper evidence</h3>{events.data?.total===0&&<p>No scanner events for this exact context.</p>}
 <details><summary>Paper outcomes by mode, payout, expiry and result</summary><p>Different contracts are not pooled. GAP/UNAVAILABLE are not losses.</p><Evidence value={paper.data?.items}/>{paper.data&&<Paging {...paper.data} change={setPaperOffset}/>}</details>
 <details><summary>Operational diagnostics and recovery state</summary><Evidence value={ops.data}/></details>
 {events.data?.items.map(e=><p key={e.id}><Link to={e.href}>Event #{e.id} · {e.state} · {e.mode} · {e.signal_time}</Link></p>)}{events.data&&<Paging {...events.data} change={setOffset}/>}
 <h3>Manual session / Journal evidence</h3><p>Separate account evidence. No automatic association with this strategy or paper outcomes.</p><Link to="/journal">Review journal</Link> · <Link to="/sessions">Review sessions</Link></>;
}
export default function Workspace(){
 const [dataset,setDataset]=useState<Dataset|null>(null),[strategy,setStrategy]=useState(0),[version,setVersion]=useState(0);
 const [dataOffset,setDataOffset]=useState(0),[strategyOffset,setStrategyOffset]=useState(0),[versionOffset,setVersionOffset]=useState(0);
 const datasets=useQuery({queryKey:['coverage',dataOffset],queryFn:()=>marketApi.coverage(dataOffset)});
 const strategies=useQuery({queryKey:['strategies',strategyOffset],queryFn:()=>researchApi.strategies(strategyOffset)});
 const versions=useQuery({queryKey:['versions',strategy,versionOffset],queryFn:()=>researchApi.versions(strategy,versionOffset),enabled:!!strategy});
 return <section className="panel"><h2>Research Workspace</h2><p>Trace evidence, not trading recommendations. Select an exact dataset and immutable version.</p>
 {[datasets,strategies,versions].map((q,i)=><Failure key={i} error={q.error}/>)}
 <label>Dataset<select aria-label="Workspace dataset" value={dataset?JSON.stringify(dataset):''} onChange={e=>setDataset(e.target.value?JSON.parse(e.target.value):null)}><option value="">Choose exact dataset</option>{datasets.data?.items.map(d=><option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{Object.values(datasetOnly(d)).join(' / ')}</option>)}</select></label>
 {datasets.isPending&&<p>Loading datasets…</p>}{datasets.data?.total===0&&<p>No datasets. <Link to="/market-data">Import market data</Link></p>}{datasets.data&&<Paging {...datasets.data} change={setDataOffset}/>}
 <label>Strategy<select aria-label="Workspace strategy" value={strategy} onChange={e=>{setStrategy(Number(e.target.value));setVersion(0);setVersionOffset(0);}}><option value={0}>Choose strategy</option>{strategies.data?.items.map(s=><option key={s.id} value={s.id}>{s.name} · #{s.id}</option>)}</select></label>{strategies.data&&<Paging {...strategies.data} change={setStrategyOffset}/>}
 <label>StrategyVersion<select aria-label="Workspace version" value={version} onChange={e=>setVersion(Number(e.target.value))}><option value={0}>Choose immutable version</option>{versions.data?.items.map(v=><option key={v.id} value={v.id}>v{v.version} · #{v.id}</option>)}</select></label>{versions.data&&<Paging {...versions.data} change={setVersionOffset}/>}
 {dataset&&version?<Context key={JSON.stringify(dataset)+version} dataset={dataset} version={version}/>:<p>No context selected. No strategy or dataset is automatically substituted.</p>}</section>;
}
export function WorkspaceEvent(){
 const id=Number(useParams().id);
 const q=useQuery({queryKey:['workspace-event',id],queryFn:()=>api(`/workspace/events/${id}`)});
 return <section className="panel"><h2>Scanner / paper lineage #{id}</h2><p>LIVE PAPER OBSERVATION or explicitly labeled REPLAY; not a broker trade.</p><Failure error={q.error}/>{q.isPending?<p>Loading evidence…</p>:<Evidence value={q.data}/>}<Link to="/workspace">Research Workspace</Link> · <Link to="/scanner">Open scanner</Link></section>;
}
