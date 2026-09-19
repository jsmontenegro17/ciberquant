import {useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {researchApi,type BacktestRun,type BacktestTrade} from '../../api/research';
import {Failure,Paging,DatasetLabel} from '../market-data/Shared';
import {ResearchWarning} from './StrategyLab';
const labels:Record<string,string>={signals_true:'Signals',trades_executed:'Executed trades',win_rate_percent:'Historical win rate %',break_even_win_rate_percent:'Break-even %',edge_percentage_points:'Observed edge (percentage points)',ev_per_resolved_trade:'EV per resolved trade',average_pnl_per_signal:'Average P&L per executed signal',total_unit_pnl:'Historical total unit P&L',max_drawdown_units:'Max drawdown (stake units)'};
export function EquityChart({curve}:{curve:NonNullable<BacktestRun['equity_curve']>}){
  const values=curve.map(p=>Number(p.equity));
  let low=0,high=0;for(const value of values){low=Math.min(low,value);high=Math.max(high,value);}
  const span=high-low||1;
  const points=values.map((v,i)=>`${50+i*700/Math.max(1,values.length-1)},${220-(v-low)*180/span}`).join(' ');
  return <figure><figcaption>Unit Equity Curve · stake units · settlement order · starts at 0</figcaption><svg viewBox="0 0 800 270" role="img" aria-label="Unit Equity Curve" style={{width:'100%'}}><text x="0" y="30" fill="currentColor">{high}</text><text x="0" y="225" fill="currentColor">{low}</text><polyline points={points} fill="none" stroke="#76bfff" strokeWidth="2"/><text x="50" y="255" fill="currentColor">0</text><text x="680" y="255" fill="currentColor">Trade {curve.length-1}</text></svg></figure>;
}
export function Backtests(){
  const [offset,setOffset]=useState(0);
  const q=useQuery({queryKey:['backtests',offset],queryFn:()=>researchApi.runs(offset)});
  return <section className="panel"><h2>Backtests</h2><ResearchWarning/><Failure error={q.error}/>{q.isPending&&<p>Loading runs…</p>}{q.data?.total===0&&<p>No runs yet.</p>}
    {q.data?.items.map(r=><p key={r.id}><Link to={`/backtests/${r.id}`}>Run #{r.id} · {r.status}</Link> · Fixed payout assumption: {r.payout_percent}% · <DatasetLabel dataset={r.dataset}/></p>)}{q.data&&<Paging {...q.data} change={setOffset}/>}</section>;
}
export function BacktestResult(){
  const id=Number(useParams().id),[offset,setOffset]=useState(0),[trade,setTrade]=useState<BacktestTrade|null>(null);
  const q=useQuery({queryKey:['backtest',id],queryFn:()=>researchApi.result(id),refetchInterval:q=>q.state.data?.status==='RUNNING'?3000:false});
  const trades=useQuery({queryKey:['backtest-trades',id,offset],queryFn:()=>researchApi.trades(id,offset),enabled:q.data?.status==='COMPLETED'});
  const r=q.data;
  return <section className="panel"><h2>Backtest #{id}</h2><ResearchWarning/><Failure error={q.error}/>{q.isPending&&<p>Loading result…</p>}
    {r&&<><p className="researchWarning">Fixed payout assumption: {r.payout_percent}% · unit stake = 1 · {r.status}</p>
      {r.error_summary&&<p role="alert">{r.error_summary}</p>}{r.status==='RUNNING'&&<p>Run is processing. A persistently RUNNING run may need recovery; do not assume completion.</p>}
      <h3>{r.strategy_snapshot.name} · v{r.strategy_snapshot.version}</h3><DatasetLabel dataset={r.dataset}/>
      <dl className="grid compact">{Object.entries({'Definition hash':r.strategy_snapshot.definition_sha256,'Config hash':r.config_sha256,'As-of Candle ID':r.as_of_candle_id,'Feature Engine':r.feature_engine_version,'Strategy DSL':r.strategy_dsl_version,'Backtest Engine':r.backtest_engine_version,'Entry Model':r.entry_model,'Expiry bars':r.expiry_bars,'Overlap policy':r.overlap_policy}).map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
      <p>{r.signal_start} inclusive → {r.signal_end} exclusive · UTC signal availability</p>
      {r.metrics&&<><h3>Historical metrics and skip evidence</h3><dl className="grid compact">{Object.entries(r.metrics).map(([k,v])=><div key={k}><dt>{labels[k]??k.replace(/_/g,' ')}</dt><dd>{v??'—'}</dd></div>)}</dl><p>— means no denominator/evidence. Draws are excluded from resolved win rate and EV, but included in average P&L per executed signal. Gross loss is a positive magnitude.</p></>}
      {r.equity_curve&&<EquityChart curve={r.equity_curve}/>}
      <h3>Trade inspector</h3><Failure error={trades.error}/><div className="tableWrap"><table><thead><tr>{['#','Signal time UTC','Entry time UTC','Expiry time UTC','Direction','Entry price','Expiry price','Result','Unit P&L','Context'].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{trades.data?.items.map(t=><tr key={t.id}><td>{t.sequence_no}</td><td>{t.signal_time}</td><td>{t.entry_time}</td><td>{t.expiry_time}</td><td>{t.direction}</td><td>{t.entry_price}</td><td>{t.expiry_price}</td><td>{t.result}</td><td>{t.unit_pnl}</td><td><button className="secondary" onClick={()=>setTrade(t)}>Inspect #{t.sequence_no}</button></td></tr>)}</tbody></table></div>
      {trades.data&&<Paging {...trades.data} change={setOffset}/>} {trade&&<section className="panel" aria-label="Signal context"><h3>Trade #{trade.sequence_no} · signal context</h3><p>field@bars_ago at {trade.signal_time} UTC</p><pre>{JSON.stringify(trade.signal_context,null,2)}</pre><button className="secondary" onClick={()=>setTrade(null)}>Close context</button></section>}
    </>}
  </section>;
}
