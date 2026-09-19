import {useEffect,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {scannerApi,type WatchItem} from '../../api/scanner';
import {researchApi} from '../../api/research';
import {marketApi,datasetOnly,type Dataset} from '../../api/marketData';
import {Failure,Paging} from '../market-data/Shared';

function Json({value}:{value:unknown}){return <pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(value,null,2)}</pre>;}
export function ScannerCard({item,onToggle}:{item:WatchItem;onToggle:()=>void}){
 const e=item.latest;
 return <section className="panel" aria-label={`Watch item ${item.id}`}>
 <h3>{item.dataset.symbol} · {item.dataset.timeframe}</h3><p>{Object.values(item.dataset).join(' / ')}</p>
 <p>{item.provider==='REPLAY'?'REPLAY MODE':item.provider} · {item.state} · {item.research_mode?'RESEARCH FILTER — not validated for normal scanning':'Validated scanner'}</p>
 <h4>{e?.strategy_name??`Version #${item.strategy_version_id}`} {e?.version?`v${e.version}`:''} · {e?.state==='MATCH'?'CONDITIONS MATCHED':e?.state??'Waiting for closed candles'}</h4>
 <p>Research direction: {e?.research_direction??'—'} · Research signal — no order sent.</p>
 <p>Validation: {e?.validation_state??'Checking'} · Dataset: {e?.dataset_validation_state??'Checking'}</p>
 <p>Current payout: {e?.current_payout??'Unavailable'} · Validation assumption: {e?.validation_payout??'Unavailable'} · Break-even %: {e?.current_break_even??'Unavailable'}</p>
 {e?.payout_warning&&<p role="alert" className="researchWarning">PAYOUT BELOW VALIDATION ASSUMPTION</p>}
 {item.state==='SUSPENDED_DEGRADED'&&<p role="alert">DEGRADED — normal scanning suspended.</p>}
 <p>Signal available: {e?.signal_time??'—'} · NEXT_CANDLE_OPEN boundary: {e?.next_entry_boundary??'—'}. Future entry price unknown.</p>
 {e?.error&&<p role="alert">{e.error}</p>}
 <details><summary>Provider health and exact signal context</summary><Json value={e?.health}/><Json value={e?.signal_context}/><Json value={e?.features}/></details>
 <button onClick={onToggle}>{item.enabled?'Pause item':'Enable item'}</button>
 </section>;
}

function Snapshot({id}:{id:number}){
 const q=useQuery({queryKey:['scanner','snapshot',id],queryFn:()=>scannerApi.snapshot(id),refetchInterval:2000});
 return <section className="panel"><h3>Live snapshot · item #{id}</h3><Failure error={q.error}/><p>FORMING is provisional, never a definitive signal. Health expires if the worker stops.</p><Json value={q.data?.subscription}/></section>;
}

export function Scanner(){
 const cache=useQueryClient(),[research,setResearch]=useState(false),[offset,setOffset]=useState(0),[eventOffset,setEventOffset]=useState(0);
 const [name,setName]=useState(''),[list,setList]=useState(0),[provider,setProvider]=useState('REPLAY'),[strategy,setStrategy]=useState(0),[version,setVersion]=useState(0),[strategyOffset,setStrategyOffset]=useState(0),[versionOffset,setVersionOffset]=useState(0),[coverageOffset,setCoverageOffset]=useState(0);
 const [dataset,setDataset]=useState<Dataset>({source:'',broker:'',symbol:'',market_type:'REGULAR',timeframe:'1m'});
 const [payout,setPayout]=useState('84'),[expiry,setExpiry]=useState(1),[selected,setSelected]=useState(0);
 const providers=useQuery({queryKey:['providers'],queryFn:scannerApi.providers});
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
 <section className="panel"><h2>Live Strategy Scanner</h2><p className="researchWarning">Research signal — no order sent. No trades, sessions, balances or ledger movements are created. Historical validation is not a guarantee. Paper observations are not historical backtests.</p>
 <h3>Providers</h3>{providers.data?.items.map(p=><details key={p.provider}><summary>{p.provider} · {p.enabled?'Enabled':'Disabled'} · {p.mode}</summary><p>{p.warning}</p><Json value={p.capabilities}/></details>)}
 {[providers,lists,items,events,coverage,strategies,versions,createList,createItem,toggle].map((q,i)=><Failure key={i} error={q.error}/>)}
 <label><input type="checkbox" checked={research} onChange={e=>{setResearch(e.target.checked);setOffset(0);}}/>Include research-only items (explicit non-validated mode)</label>
 </section>
 <section className="panel formPanel"><h3>Watchlist configuration</h3>
 <form onSubmit={e=>{e.preventDefault();createList.mutate(name);}}><label>Watchlist name<input required maxLength={120} value={name} onChange={e=>setName(e.target.value)}/></label><button disabled={createList.isPending}>Create watchlist</button></form>
 <form onSubmit={e=>{e.preventDefault();createItem.mutate({list,body:{provider,dataset,strategy_version_id:version,research_mode:research,...(research?{research_payout:payout,research_expiry:expiry}:{})}});}}>
 <label>Watchlist<select required value={list||''} onChange={e=>setList(Number(e.target.value))}><option value="">Select watchlist</option>{lists.data?.items.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
 <label>Provider<select value={provider} onChange={e=>setProvider(e.target.value)}>{['REPLAY','MT5','IQOPTION'].map(p=><option key={p}>{p}</option>)}</select></label>
 <label>Existing dataset<select value="" onChange={e=>setDataset(JSON.parse(e.target.value))}><option value="">Select dataset or enter full identity below</option>{coverage.data?.items.map(d=><option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{Object.values(datasetOnly(d)).join(' / ')}</option>)}</select></label>
 {coverage.data&&<Paging {...coverage.data} change={setCoverageOffset}/>}
 <div className="grid compact">{(['source','broker','symbol'] as const).map(k=><label key={k}>{k}<input required value={dataset[k]} onChange={e=>setDataset({...dataset,[k]:e.target.value})}/></label>)}<label>Market type<select value={dataset.market_type} onChange={e=>setDataset({...dataset,market_type:e.target.value})}><option>REGULAR</option><option>OTC</option></select></label><label>Timeframe<select value={dataset.timeframe} onChange={e=>setDataset({...dataset,timeframe:e.target.value})}>{['1m','5m','15m','30m','1h'].map(t=><option key={t}>{t}</option>)}</select></label></div>
 <label>Strategy<select required value={strategy||''} onChange={e=>{setStrategy(Number(e.target.value));setVersion(0);setVersionOffset(0);}}><option value="">Select strategy</option>{strategies.data?.items.map(s=><option key={s.id} value={s.id}>{s.name} · {s.status}</option>)}</select></label>{strategies.data&&<Paging {...strategies.data} change={setStrategyOffset}/>}
 <label>Immutable version<select required value={version||''} onChange={e=>setVersion(Number(e.target.value))}><option value="">Select version</option>{versions.data?.items.map(v=><option key={v.id} value={v.id}>v{v.version} · {v.validation_state??'NOT_VALIDATED'}</option>)}</select></label>{versions.data&&<Paging {...versions.data} change={setVersionOffset}/>}
 <p>Normal items require TESTING and historical PASS on this exact source / broker / symbol / market type / timeframe. The backend verifies compatibility; global PASS alone is not enough.</p>
 {research&&<div className="grid compact"><label>Research paper payout %<input required value={payout} onChange={e=>setPayout(e.target.value)}/></label><label>Research expiry bars<input type="number" min={1} max={60} value={expiry} onChange={e=>setExpiry(Number(e.target.value))}/></label></div>}
 <button disabled={!list||!version||createItem.isPending}>Create watch item / start provider</button></form></section>
 <section aria-label="Watched datasets"><h2>Watched datasets</h2>{items.data?.total===0&&<p>No watch items in this filter.</p>}{items.data?.items.map(item=><div key={item.id}><ScannerCard item={item} onToggle={()=>toggle.mutate({id:item.id,enabled:!item.enabled})}/><button onClick={()=>setSelected(item.id)}>Inspect snapshot #{item.id}</button></div>)}{items.data&&<Paging {...items.data} change={setOffset}/>}</section>
 {selected>0&&<Snapshot id={selected}/>}
 <section className="panel"><h2>Event history</h2><div className="tableWrap"><table><thead><tr>{['Time / Mode','Dataset','Strategy / Direction','State','Payout / Validation','Paper observation'].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{events.data?.items.map(e=><tr key={e.id}><td>{e.signal_time}<br/>{e.mode==='REPLAY'?'REPLAY MODE':e.mode}</td><td>{Object.values(e.dataset).join(' / ')}</td><td>#{e.strategy_version_id} · {e.direction}</td><td>{e.state}</td><td>{e.current_payout??'Unavailable'} / {e.validation_state_snapshot}</td><td>{e.paper_outcome?<details><summary>{e.mode==='REPLAY'?'REPLAY PAPER OBSERVATION':'LIVE PAPER OBSERVATION'} · {e.paper_outcome.result}</summary><Json value={e.paper_outcome.evidence}/></details>:e.state==='MATCH'?'Pending future observed candles':'—'}</td></tr>)}</tbody></table></div>{events.data&&<Paging {...events.data} change={setEventOffset}/>}</section>
 </>;
}
