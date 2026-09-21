import { codeLabel } from '../../utils/spanish';
import {useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {researchApi,type BacktestRun,type BacktestTrade} from '../../api/research';
import {Failure,Paging,DatasetLabel} from '../market-data/Shared';
import {ResearchWarning} from './StrategyLab';
const labels:Record<string,string>={signals_true:"Señales",trades_executed:"Operaciones ejecutadas",win_rate_percent:"Porcentaje histórico de aciertos",break_even_win_rate_percent:"Punto de equilibrio %",edge_percentage_points:"Ventaja observada (puntos porcentuales)",ev_per_resolved_trade:'Valor esperado por operación resuelta',average_pnl_per_signal:"Resultado neto medio por señal ejecutada",total_unit_pnl:"Resultado neto histórico total en unidades",max_drawdown_units:"Máxima caída acumulada (unidades de importe)"};
export function EquityChart({curve}:{curve:NonNullable<BacktestRun['equity_curve']>}){
  const values=curve.map(p=>Number(p.equity));
  let low=0,high=0;for(const value of values){low=Math.min(low,value);high=Math.max(high,value);}
  const span=high-low||1;
  const points=values.map((v,i)=>`${50+i*700/Math.max(1,values.length-1)},${220-(v-low)*180/span}`).join(' ');
  return <figure><figcaption>Curva acumulada · unidades de importe · orden de liquidación · comienza en 0</figcaption><svg viewBox="0 0 800 270" role="img" aria-label="Curva de resultado acumulado en unidades" style={{width:'100%'}}><text x="0" y="30" fill="currentColor">{high}</text><text x="0" y="225" fill="currentColor">{low}</text><polyline points={points} fill="none" stroke="#76bfff" strokeWidth="2"/><text x="50" y="255" fill="currentColor">0</text><text x="680" y="255" fill="currentColor">Operación {curve.length-1}</text></svg></figure>;
}
export function Backtests(){
  const [offset,setOffset]=useState(0);
  const q=useQuery({queryKey:['backtests',offset],queryFn:()=>researchApi.runs(offset)});
  return <section className="panel"><h2>Pruebas históricas</h2><ResearchWarning/><Failure error={q.error}/>{q.isPending&&<p>Cargando ejecuciones…</p>}{q.data?.total===0&&<p>Todavía no hay ejecuciones.</p>}
    {q.data?.items.map(r=><p key={r.id}><Link to={`/backtests/${r.id}`}>Ejecución n.º{r.id} · {codeLabel(r.status)}</Link> · Supuesto de rendimiento fijo: {r.payout_percent}% · <DatasetLabel dataset={r.dataset}/></p>)}{q.data&&<Paging {...q.data} change={setOffset}/>}</section>;
}
export function BacktestResult(){
  const id=Number(useParams().id),[offset,setOffset]=useState(0),[trade,setTrade]=useState<BacktestTrade|null>(null);
  const q=useQuery({queryKey:['backtest',id],queryFn:()=>researchApi.result(id),refetchInterval:q=>q.state.data?.status==='RUNNING'?3000:false});
  const trades=useQuery({queryKey:['backtest-trades',id,offset],queryFn:()=>researchApi.trades(id,offset),enabled:q.data?.status==='COMPLETED'});
  const r=q.data;
  return <section className="panel"><h2>Prueba histórica n.º{id}</h2><ResearchWarning/><Failure error={q.error}/>{q.isPending&&<p>Cargando resultado…</p>}
    {r&&<><p className="researchWarning">Supuesto de rendimiento fijo: {r.payout_percent}% · importe unitario = 1 · {codeLabel(r.status)}</p>
      {r.error_summary&&<p role="alert">{r.error_summary}</p>}{r.status==='RUNNING'&&<p>La ejecución está en proceso. Si permanece en RUNNING puede requerir recuperación; no la consideres terminada.</p>}
      <h3>{r.strategy_snapshot.name} · v{r.strategy_snapshot.version}</h3><DatasetLabel dataset={r.dataset}/>
      <dl className="grid compact">{Object.entries({"Huella de definición":r.strategy_snapshot.definition_sha256,"Huella de configuración":r.config_sha256,"ID de vela de corte":r.as_of_candle_id,"Motor de indicadores":r.feature_engine_version,"Lenguaje de estrategia (DSL)":r.strategy_dsl_version,"Motor de pruebas históricas":r.backtest_engine_version,"Modelo de entrada":r.entry_model,"Velas hasta vencimiento":r.expiry_bars,"Política de superposición":r.overlap_policy}).map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
      <p>{r.signal_start} inclusivo → {r.signal_end} exclusivo · disponibilidad de señal UTC</p>
      {r.metrics&&<><h3>Métricas históricas y evidencia de omisiones</h3><dl className="grid compact">{Object.entries(r.metrics).map(([k,v])=><div key={k}><dt>{labels[k]??k.replace(/_/g,' ')}</dt><dd>{v??'—'}</dd></div>)}</dl><p>— indica ausencia de denominador o evidencia. Los empates se excluyen del porcentaje de aciertos y del valor esperado, pero se incluyen en el resultado neto medio por señal ejecutada. La pérdida bruta es una magnitud positiva.</p></>}
      {r.equity_curve&&<EquityChart curve={r.equity_curve}/>}
      <h3>Inspección de operaciones</h3><Failure error={trades.error}/><div className="tableWrap"><table><thead><tr>{['#',"Hora de señal UTC","Hora de entrada UTC","Hora de vencimiento UTC","Dirección","Precio de entrada","Precio de vencimiento","Resultado","Resultado neto en unidades","Contexto"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{trades.data?.items.map(t=><tr key={t.id}><td>{t.sequence_no}</td><td>{t.signal_time}</td><td>{t.entry_time}</td><td>{t.expiry_time}</td><td>{codeLabel(t.direction)}</td><td>{t.entry_price}</td><td>{t.expiry_price}</td><td>{codeLabel(t.result)}</td><td>{t.unit_pnl}</td><td><button className="secondary" onClick={()=>setTrade(t)}>Inspeccionar n.º{t.sequence_no}</button></td></tr>)}</tbody></table></div>
      {trades.data&&<Paging {...trades.data} change={setOffset}/>} {trade&&<section className="panel" aria-label="Contexto de señal"><h3>Operación n.º{trade.sequence_no} · contexto de señal</h3><p>campo@velas_anteriores en {trade.signal_time} UTC</p><pre>{JSON.stringify(trade.signal_context,null,2)}</pre><button className="secondary" onClick={()=>setTrade(null)}>Cerrar contexto</button></section>}
    </>}
  </section>;
}
