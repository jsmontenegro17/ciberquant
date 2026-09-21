import { codeLabel } from '../../utils/spanish';
import {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {useQuery,useMutation} from '@tanstack/react-query';
import {marketApi,datasetOnly,type Coverage} from '../../api/marketData';
import {researchApi,type Version,type RunInput} from '../../api/research';
import {Failure,Paging} from '../market-data/Shared';
export function RunSetup({version}:{version:Version}){
  const navigate=useNavigate();
  const [offset,setOffset]=useState(0),[dataset,setDataset]=useState<Coverage|null>(null);
  const [start,setStart]=useState(''),[end,setEnd]=useState(''),[asOf,setAsOf]=useState(''),[payout,setPayout]=useState('84'),[expiry,setExpiry]=useState(1),[overlap,setOverlap]=useState('ALLOW');
  const coverage=useQuery({queryKey:['coverage',offset],queryFn:()=>marketApi.coverage(offset)});
  const run=useMutation({mutationFn:(body:RunInput)=>researchApi.run(body),onSuccess:r=>navigate(`/backtests/${r.id}`)});
  return <section className="panel formPanel"><h2>Ejecutar prueba histórica · v{version.version}</h2><p className="researchWarning">Supuesto de rendimiento fijo: {payout}%. Importe unitario = 1. Entrada en la apertura siguiente (NEXT_CANDLE_OPEN). Sin modelo de rendimiento histórico, latencia o diferencial de precios.</p><Failure error={coverage.error}/><Failure error={run.error}/>
    <form onSubmit={e=>{e.preventDefault();if(dataset)run.mutate({strategy_version_id:version.id,dataset:datasetOnly(dataset),signal_start:start,signal_end:end,as_of_candle_id:asOf?Number(asOf):null,payout_percent:payout,expiry_bars:expiry,overlap_policy:overlap});}}>
      <label>Conjunto de datos<select required value={dataset?JSON.stringify(datasetOnly(dataset)):''} onChange={e=>{const d=coverage.data?.items.find(d=>JSON.stringify(datasetOnly(d))===e.target.value)??null;setDataset(d);setStart(d?.first_candle??'');setEnd(d?new Date(Date.parse(d.last_candle)+1).toISOString():'');setAsOf('');}}><option value="">Selecciona un conjunto de datos</option>{coverage.data?.items.map(d=><option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{d.source} / {d.broker} / {d.symbol} / {d.market_type} / {d.timeframe}</option>)}</select></label>
      <label>Inicio inclusivo de señales (con zona horaria)<input required value={start} onChange={e=>setStart(e.target.value)}/></label><label>Fin exclusivo de señales (con zona horaria)<input required value={end} onChange={e=>setEnd(e.target.value)}/></label>
      <p>Las señales usan la hora de cierre. Solo se cuentan resultados cuyo vencimiento no supera el fin de señales. Ajusta ese límite para incluir las velas completadas deseadas.</p>
      <div className="grid compact"><label>ID de vela de corte<input type="number" min="0" step="1" value={asOf} onChange={e=>setAsOf(e.target.value)}/></label><label>Rendimiento %<input required type="number" min="0.000001" max="100" step="0.000001" value={payout} onChange={e=>setPayout(e.target.value)}/></label><label>Velas hasta vencimiento<input required type="number" min="1" max="60" step="1" value={expiry} onChange={e=>setExpiry(Number(e.target.value))}/></label><label>Política de superposición<select value={overlap} onChange={e=>setOverlap(e.target.value)}><option value={"ALLOW"}>{codeLabel("ALLOW")}</option><option value={"SKIP_UNTIL_EXPIRY"}>{codeLabel("SKIP_UNTIL_EXPIRY")}</option></select></label></div>
      <button disabled={run.isPending||!dataset}>{run.isPending?"Ejecutando…":"Iniciar prueba histórica"}</button>
    </form>{coverage.data&&<Paging {...coverage.data} change={n=>{setOffset(n);setDataset(null);}}/>}
  </section>;
}
