import { codeLabel, evidenceText } from '../../utils/spanish';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { featureApi, type Spec, type ComputeRequest, type FeatureResult } from '../../api/features';
import { marketApi, datasetOnly, type Coverage } from '../../api/marketData';
import { DatasetLabel, Failure, Paging } from '../market-data/Shared';
import { FeatureChart, displayValue } from './FeatureChart';

export function FeatureResults({ result }: { result: FeatureResult }) {
  const [offset, setOffset] = useState(0);
  const m = result.metadata;
  return <section className="panel" aria-label="Resultados de indicadores"><h2>Instantánea de datos</h2><DatasetLabel dataset={m.dataset} />
    <dl className="grid compact">{Object.entries({ "Versión del cálculo": m.calculation_version, "ID de vela de corte": m.as_of_candle_id, "Inicio del cálculo": m.calculation_anchor ?? '—', "Velas procesadas": m.candles_processed, "Filas devueltas": m.rows_returned }).map(([k,v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
    <p>{m.requested_start} inclusivo → {m.requested_end} exclusivo · UTC</p>
    {result.rows.length === 0 ? <p>No hay velas en esta instantánea o intervalo.</p> : <FeatureChart result={result} />}
    <p>— significa no disponible o preparación inicial, no cero. Los valores están disponibles al cierre de vela. Los huecos no reinician indicadores.</p>
    <div className="tableWrap"><table aria-label="Filas de indicadores"><thead><tr>{["Hora (UTC)", 'O', 'H', 'L', 'C', "Dirección", "Segundos sin datos", "Ejecución", ...result.feature_keys].map(k => <th key={k}>{k}</th>)}</tr></thead>
      <tbody>{result.rows.slice(offset, offset + 20).map(r => <tr key={r.candle_id}><td>{r.open_time}</td><td>{r.open}</td><td>{r.high}</td><td>{r.low}</td><td>{r.close}</td><td>{codeLabel(r.direction)}</td><td>{r.gap_before ? '⚠ ' : ''}{r.gap_seconds}</td><td>{r.contiguous_run_length}</td>{result.feature_keys.map(k => <td key={k}>{displayValue(r.features[k])}</td>)}</tr>)}</tbody></table></div>
    <Paging offset={offset} limit={20} total={result.rows.length} change={setOffset} />
  </section>;
}
export function FeatureLab() {
  const [offset, setOffset] = useState(0);
  const coverage = useQuery({ queryKey: ['coverage', offset], queryFn: () => marketApi.coverage(offset) });
  const definitions = useQuery({ queryKey: ['feature-definitions'], queryFn: featureApi.definitions });
  const [dataset, setDataset] = useState<Coverage | null>(null);
  const [start, setStart] = useState(''), [end, setEnd] = useState(''), [asOf, setAsOf] = useState('');
  const [specs, setSpecs] = useState<Spec[]>([]);
  const [include, setInclude] = useState(true);
  const analysis = useMutation({ mutationFn: (request: ComputeRequest) => featureApi.compute(request) });
  const def = definitions.data;
  const changeSpec = (i: number, value: Spec) => { setSpecs(specs.map((s, index) => index === i ? value : s)); analysis.reset(); };
  return <div><section className="panel formPanel"><h2>Indicadores</h2>
    <p>Indicadores reproducibles para investigar, no señales para operar. La configuración predefinida no es una estrategia.</p>
    <Failure error={definitions.error} /><Failure error={coverage.error} />
    {(definitions.isPending || coverage.isPending) && <p>Cargando definiciones y datos…</p>}
    {coverage.data?.total === 0 && <p>No hay datos disponibles. Solicita la importación a un administrador.</p>}
    <form onSubmit={e => { e.preventDefault(); if (dataset) analysis.mutate({ dataset: datasetOnly(dataset), start, end, as_of_candle_id: asOf ? Number(asOf) : null, indicators: specs, include_candle_features: include }); }}>
      <label>Conjunto de datos<select required aria-label="Conjunto de datos" value={dataset ? JSON.stringify(datasetOnly(dataset)) : ''} onChange={e => {
        const next = coverage.data?.items.find(d => JSON.stringify(datasetOnly(d)) === e.target.value) ?? null;
        setDataset(next); setStart(next?.first_candle ?? ''); setEnd(next ? new Date(Date.parse(next.last_candle) + 1).toISOString() : ''); setAsOf(''); analysis.reset();
      }}><option value="">Selecciona un conjunto de datos</option>{coverage.data?.items.map(d => <option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{d.source} / {d.broker} / {d.symbol} / {d.market_type} / {d.timeframe}</option>)}</select></label>
      <div className="grid compact"><label>Inicio inclusivo (con zona horaria)<input required value={start} onChange={e => { setStart(e.target.value); analysis.reset(); }} /></label>
        <label>Fin exclusivo (con zona horaria)<input required value={end} onChange={e => { setEnd(e.target.value); analysis.reset(); }} /></label>
        <label>ID de vela de corte (vacío = última)<input type="number" min="0" step="1" value={asOf} onChange={e => { setAsOf(e.target.value); analysis.reset(); }} /></label></div>
      <label className="checkboxLabel"><input type="checkbox" checked={include} onChange={e => { setInclude(e.target.checked); analysis.reset(); }} />Incluir características de velas</label>
      <button type="button" disabled={!def} onClick={() => { setSpecs(def!.defaults.STANDARD.map(s => ({...s}))); analysis.reset(); }}>Cargar conjunto estándar</button>
      {specs.map((s, i) => { const d = def?.supported_indicators.find(x => x.type === s.type); return <div className="grid compact" key={i}>
        <label>Indicador {i+1}<select value={s.type} onChange={e => { const next = def!.supported_indicators.find(x => x.type === e.target.value)!; changeSpec(i, { type: next.type, ...next.parameters }); }}>{def?.supported_indicators.map(x => <option key={x.type} value={x.type}>{codeLabel(x.type)}</option>)}</select></label>
        <label>Período {i+1}<input type="number" required min={d?.constraints.period.min} max={d?.constraints.period.max} step="1" value={s.period} onChange={e => changeSpec(i, {...s, period: Number(e.target.value)})} /></label>
        {d?.constraints.stddev_multiplier && <label>Multiplicador {i+1}<input required type="number" min="0.000001" max={d.constraints.stddev_multiplier.max} step="0.000001" value={s.stddev_multiplier} onChange={e => changeSpec(i, {...s, stddev_multiplier: e.target.value})} /></label>}
        <small>Preparación inicial: {evidenceText(d?.warmup_definition)}</small><button type="button" className="secondary" onClick={() => { setSpecs(specs.filter((_, n) => n !== i)); analysis.reset(); }}>Quitar {i+1}</button>
      </div>; })}
      <div className="actions"><button type="button" disabled={!def || specs.length >= def.max_indicator_specs} onClick={() => { const d = def!.supported_indicators[0]; setSpecs([...specs, {type: d.type, ...d.parameters}]); analysis.reset(); }}>Añadir indicador</button>
        <button disabled={!dataset || !def || analysis.isPending}>{analysis.isPending ? "Analizando…" : "Analizar"}</button></div>
    </form>
    {coverage.data && <Paging {...coverage.data} change={n => { setOffset(n); setDataset(null); analysis.reset(); }} />}
    <Failure error={analysis.error} />
  </section>{analysis.data && !analysis.isPending && !analysis.isError && <FeatureResults key={analysis.submittedAt} result={analysis.data} />}</div>;
}
