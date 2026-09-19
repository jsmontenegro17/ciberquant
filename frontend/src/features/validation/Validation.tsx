import {useState} from 'react';
import {Link,useNavigate,useParams,useSearchParams} from 'react-router-dom';
import {useQuery,useMutation,useQueryClient} from '@tanstack/react-query';
import {validationApi,type ValidationInput,type Metrics,type ValidationRun} from '../../api/validation';
import {marketApi,datasetOnly,type Coverage} from '../../api/marketData';
import {Failure,Paging} from '../market-data/Shared';

export function ValidationWarning(){return <p className="researchWarning">Historical validation does not guarantee future profitability. Live/paper evidence remains separate. OOS means outside the development region of this workflow; CiberQuant cannot guarantee that raw holdout data was never inspected externally. Fixed payout assumption; unit stake only.</p>;}
function Reuse({run}:{run:ValidationRun}){const w=run.holdout_warnings;return <section aria-label="Research history"><p>Prior attempts: {w.prior_validation_count} · Previously revealed: {w.prior_revealed_holdout_count} · Overlapping: {w.overlapping_holdout_count}</p>{w.overlapping_holdout_count>0&&<p className="researchWarning">REUSED HOLDOUT — not independent evidence.</p>}{w.replay_count>0&&<p className="researchWarning">REPLAY — not new independent evidence.</p>}</section>;}
const metricKeys=['trades_executed','wins','losses','draws','resolved_trades','win_rate_percent','break_even_win_rate_percent','edge_percentage_points','ev_per_resolved_trade','total_unit_pnl','max_drawdown_units'];
const metricLabels=['Trades','Wins','Losses','Draws','Resolved','WR %','Break-even %','Edge pp','EV','Units','DD units'];
function MetricsTable({rows}:{rows:{label:string;metrics:Metrics}[]}){return <div className="tableWrap"><table><thead><tr><th>Segment</th>{metricLabels.map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{rows.map(r=><tr key={r.label}><th>{r.label}</th>{metricKeys.map(k=><td key={k}>{r.metrics[k]??'—'}</td>)}</tr>)}</tbody></table></div>;}

export function ValidationList(){
 const [offset,setOffset]=useState(0);
 const q=useQuery({queryKey:['validations',offset],queryFn:()=>validationApi.list(offset)});
 return <section className="panel"><h2>Validation</h2><ValidationWarning/><p>Create a plan from a TESTING strategy's immutable version in <Link to="/strategies">Strategy Lab</Link>.</p><Failure error={q.error}/>{q.isPending&&<p>Loading validation history…</p>}{q.data?.total===0&&<p>No validation plans yet.</p>}<div className="tableWrap"><table><thead><tr>{['Plan / Version','Dataset','Status / Test','Verdict','Validation state','Created'].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{q.data?.items.map(r=><tr key={r.id}><td><Link to={`/validation/${r.id}`}>{r.strategy_name?`${r.strategy_name} · `:''}Plan #{r.id} / version #{r.version_number??r.strategy_version_id}</Link></td><td>{Object.values(r.dataset).join(' / ')}</td><td>{r.status} / {r.test_revealed_at?'REVEALED':'Not revealed'}</td><td>{r.verdict}</td><td>{r.validation_state}</td><td>{r.created_at}</td></tr>)}</tbody></table></div>{q.data&&<Paging {...q.data} change={setOffset}/>}</section>;
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
 return <section className="panel formPanel"><h2>Validate immutable version #{version}</h2><ValidationWarning/><Failure error={coverage.error}/><Failure error={protocol.error}/><Failure error={preview.error}/><Failure error={create.error}/>
 {protocol.data&&<p>{protocol.data.validation_engine_version} · Split {protocol.data.split.join(' / ')} · {protocol.data.fold_count} folds · {protocol.data.bootstrap.iterations} bootstrap iterations. Test minimum: {protocol.data.minimum_resolved} resolved / {protocol.data.minimum_active_days} active UTC days.</p>}
 <form onChange={()=>preview.reset()} onSubmit={e=>{e.preventDefault();preview.mutate(input());}}>
 <label>Dataset<select required value={dataset?JSON.stringify(datasetOnly(dataset)):''} onChange={e=>{const d=coverage.data?.items.find(x=>JSON.stringify(datasetOnly(x))===e.target.value)??null;setDataset(d);setStart(d?.first_candle??'');setEnd(d?new Date(Date.parse(d.last_candle)+1).toISOString():'');}}><option value="">Select dataset</option>{coverage.data?.items.map(d=><option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{Object.values(datasetOnly(d)).join(' / ')}</option>)}</select></label>
 <label>Overall start (UTC)<input required value={start} onChange={e=>setStart(e.target.value)}/></label><label>Overall end (UTC)<input required value={end} onChange={e=>setEnd(e.target.value)}/></label>
 <p>Set overall end to the desired last candle close. Signals are close-time based; outcomes must finish inside their partition.</p>
 <div className="grid compact"><label>As-of candle ID<input type="number" min="0" value={asOf} onChange={e=>setAsOf(e.target.value)}/></label><label>Payout %<input required value={payout} onChange={e=>setPayout(e.target.value)}/></label><label>Expiry bars<input required type="number" min="1" max="60" value={expiry} onChange={e=>setExpiry(Number(e.target.value))}/></label><label>Overlap policy<select value={overlap} onChange={e=>setOverlap(e.target.value)}><option>ALLOW</option><option>SKIP_UNTIL_EXPIRY</option></select></label></div>
 <button disabled={!dataset||!version||preview.isPending||create.isPending}>Preview frozen plan</button></form>
 {coverage.data&&<Paging {...coverage.data} change={n=>{setOffset(n);setDataset(null);preview.reset();}}/>}
 {frozen&&<section aria-label="Plan preview"><h3>Plan preview</h3><p>Dataset: {Object.values(frozen.dataset).join(' / ')} · As-of snapshot: {frozen.as_of_candle_id}</p><p>{frozen.overall_start} → {frozen.overall_end}</p><p>Payout {frozen.payout_percent}% · Expiry {frozen.expiry_bars} · {frozen.overlap_policy}</p><ul>{frozen.boundaries.map(b=><li key={b.segment_type+b.fold_number}>{b.segment_type} {b.fold_number||''}: {b.signal_start} → {b.signal_end}</li>)}</ul><p>Creating this validation freezes the strategy version, dataset snapshot and split boundaries.</p><button disabled={create.isPending} onClick={()=>{const {strategy_version_id,dataset,overall_start,overall_end,as_of_candle_id,payout_percent,expiry_bars,overlap_policy}=frozen;create.mutate({strategy_version_id,dataset,overall_start,overall_end,as_of_candle_id,payout_percent,expiry_bars,overlap_policy});}}>{create.isPending?'Computing development…':'Create Validation Plan'}</button></section>}
 </section>;
}

export function ValidationDetail(){
 const id=Number(useParams().id),cache=useQueryClient(),[confirm,setConfirm]=useState(false);
 const q=useQuery({queryKey:['validation',id],queryFn:()=>validationApi.detail(id),refetchInterval:q=>q.state.data?.status.startsWith('RUNNING')?3000:false});
 const segments=useQuery({queryKey:['validation-segments',id,q.data?.status],queryFn:()=>validationApi.segments(id)});
 const reveal=useMutation({mutationFn:()=>validationApi.reveal(id),onSuccess:r=>{cache.setQueryData(['validation',id],r);cache.invalidateQueries({queryKey:['versions']});cache.invalidateQueries({queryKey:['validations']});setConfirm(false);}});
 const r=q.data;
 return <section className="panel"><h2>Validation evidence #{id}</h2><ValidationWarning/><Failure error={q.error}/><Failure error={segments.error}/><Failure error={reveal.error}/>{q.isPending&&<p>Loading evidence…</p>}{r&&<>
 <p>{r.validation_engine_version} · {r.status} · {r.validation_state} · Latest attempt: {r.latest_validation_attempt}</p><p>Config hash: {r.config_sha256}</p><p>Definition hash: {r.config_snapshot.definition_sha256}</p><p>Version #{r.strategy_version_id} · {Object.values(r.dataset).join(' / ')} · As-of {r.as_of_candle_id} · {r.overall_start} → {r.overall_end}</p><p>Fixed payout assumption: {r.payout_percent}% · Expiry {r.expiry_bars} · {r.overlap_policy}</p><Reuse run={r}/>{r.error_summary&&<p role="alert">{r.error_summary}</p>}
 <h3>PRELIMINARY EVIDENCE</h3>{r.development_summary&&<MetricsTable rows={Object.entries(r.development_summary).map(([label,metrics])=>({label,metrics}))}/>}
 <h3>Walk-forward evaluation of a fixed strategy</h3><p>No retraining, optimization or threshold search. Expanding canonical-origin context.</p>
 {r.walk_forward_summary?.map(f=><section key={f.fold_number}><h4>Fold {f.fold_number} · {f.evaluable?'Evaluable':'Insufficient'}</h4><p>{r.config_snapshot.boundaries.find(b=>b.fold_number===f.fold_number)?.signal_start} → {r.config_snapshot.boundaries.find(b=>b.fold_number===f.fold_number)?.signal_end}</p><MetricsTable rows={[{label:`Fold ${f.fold_number}`,metrics:Object.fromEntries(Object.entries(f).filter(([,v])=>typeof v!=='boolean')) as Metrics}]}/></section>)}
 <section aria-label="Final test"><h3>FINAL TEST — {r.test_revealed_at?'REVEALED':r.status==='SEALED'?'SEALED':'NOT REVEALED'}</h3><p>{r.config_snapshot.boundaries.find(b=>b.segment_type==='TEST')?.signal_start} → {r.config_snapshot.boundaries.find(b=>b.segment_type==='TEST')?.signal_end}</p>
 {!r.test_revealed_at&&<p>Not calculated. No test trades, metrics or bootstrap exist.</p>}
 {r.status==='SEALED'&&!confirm&&<button onClick={()=>setConfirm(true)}>Reveal Final Test</button>}
 {confirm&&<section role="dialog" aria-label="Confirm reveal"><p>Once revealed, this holdout can no longer be considered unseen within this validation workflow.</p><button disabled={reveal.isPending} onClick={()=>reveal.mutate()}>Confirm irreversible reveal</button><button disabled={reveal.isPending} onClick={()=>setConfirm(false)}>Cancel</button></section>}
 {r.test_summary&&<MetricsTable rows={[{label:'FINAL TEST',metrics:r.test_summary}]}/>}
 {r.bootstrap_summary&&<section aria-label="Bootstrap evidence"><h4>95% UTC day-block bootstrap interval</h4><p>Mean unit P&amp;L: {r.bootstrap_summary.point_estimate??'—'} · [{r.bootstrap_summary.lower_95??'—'}, {r.bootstrap_summary.upper_95??'—'}]</p><p>UTC day blocks: {r.bootstrap_summary.block_count} · Iterations: {r.bootstrap_summary.iterations}</p><p>Seed: {r.bootstrap_summary.seed}</p><p>Preserves intraday dependence; does not establish independence between days or probability of future profit.</p></section>}
 </section><h3>{r.verdict==='PASS'?'Historical validation PASS':r.verdict}</h3>{r.gates&&<ul>{Object.entries(r.gates).map(([gate,pass])=><li key={gate}>{pass?'✓':r.verdict==='INCONCLUSIVE'&&['test_resolved','test_days','evaluable_folds'].includes(gate)?'insufficient':'✗'} {gate}</li>)}</ul>}
 {r.temporal_stability&&Object.entries(r.temporal_stability).map(([kind,months])=><section key={kind}><h3>{kind} · UTC monthly descriptive stability</h3><p>Month-level outcomes are descriptive, not extra PASS gates.</p><MonthlyChart months={months}/><MetricsTable rows={months.map(m=>({label:m.month,metrics:m}))}/></section>)}
 <h3>Immutable child evidence</h3><ul>{segments.data?.map(s=><li key={s.id}>{s.segment_type} {s.fold_number||''}: {s.backtest_run_id?<Link to={`/backtests/${s.backtest_run_id}`}>Inspect child #{s.backtest_run_id}</Link>:'Not calculated'}</li>)}</ul>
 </>}</section>;
}

function MonthlyChart({months}:{months:(Metrics&{month:string})[]}){
 const values=months.map(m=>Number(m.total_unit_pnl)),extent=Math.max(1,...values.map(Math.abs));
 return <svg role="img" aria-label="Monthly unit P&L (descriptive)" viewBox={`0 0 600 ${Math.max(40,months.length*32)}`} style={{width:'100%',maxHeight:300}}>{months.map((m,i)=><g key={m.month}><text x="0" y={i*32+20} fill="currentColor" fontSize="12">{m.month}</text><line x1="330" y1={i*32} x2="330" y2={i*32+28} stroke="gray"/><rect x={values[i]<0?330+values[i]/extent*220:330} y={i*32+4} width={Math.abs(values[i])/extent*220} height="20" fill="#739db8"/></g>)}</svg>;
}
