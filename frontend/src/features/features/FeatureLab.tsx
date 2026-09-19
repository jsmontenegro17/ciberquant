import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { featureApi, type Spec, type ComputeRequest, type FeatureResult } from '../../api/features';
import { marketApi, datasetOnly, type Coverage } from '../../api/marketData';
import { DatasetLabel, Failure, Paging } from '../market-data/Shared';
import { FeatureChart, displayValue } from './FeatureChart';

export function FeatureResults({ result }: { result: FeatureResult }) {
  const [offset, setOffset] = useState(0);
  const m = result.metadata;
  return <section className="panel" aria-label="Feature results"><h2>Dataset snapshot</h2><DatasetLabel dataset={m.dataset} />
    <dl className="grid compact">{Object.entries({ 'Calculation version': m.calculation_version, 'As-of candle ID': m.as_of_candle_id, 'Calculation anchor': m.calculation_anchor ?? '—', 'Candles processed': m.candles_processed, 'Rows returned': m.rows_returned }).map(([k,v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
    <p>{m.requested_start} inclusive → {m.requested_end} exclusive · UTC</p>
    {result.rows.length === 0 ? <p>No candles in this snapshot/range.</p> : <FeatureChart result={result} />}
    <p>— = unavailable / warmup, not zero. Values become available at candle close. Gaps do not reset indicators.</p>
    <div className="tableWrap"><table aria-label="Feature rows"><thead><tr>{['Time (UTC)', 'O', 'H', 'L', 'C', 'Direction', 'Gap seconds', 'Run', ...result.feature_keys].map(k => <th key={k}>{k}</th>)}</tr></thead>
      <tbody>{result.rows.slice(offset, offset + 20).map(r => <tr key={r.candle_id}><td>{r.open_time}</td><td>{r.open}</td><td>{r.high}</td><td>{r.low}</td><td>{r.close}</td><td>{r.direction}</td><td>{r.gap_before ? '⚠ ' : ''}{r.gap_seconds}</td><td>{r.contiguous_run_length}</td>{result.feature_keys.map(k => <td key={k}>{displayValue(r.features[k])}</td>)}</tr>)}</tbody></table></div>
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
  return <div><section className="panel formPanel"><h2>Feature Lab</h2>
    <p>Deterministic research features, not trading signals. Preset for research convenience — not a strategy.</p>
    <Failure error={definitions.error} /><Failure error={coverage.error} />
    {(definitions.isPending || coverage.isPending) && <p>Loading definitions and datasets…</p>}
    {coverage.data?.total === 0 && <p>No datasets available. Ask an administrator to import data.</p>}
    <form onSubmit={e => { e.preventDefault(); if (dataset) analysis.mutate({ dataset: datasetOnly(dataset), start, end, as_of_candle_id: asOf ? Number(asOf) : null, indicators: specs, include_candle_features: include }); }}>
      <label>Dataset<select required aria-label="Dataset" value={dataset ? JSON.stringify(datasetOnly(dataset)) : ''} onChange={e => {
        const next = coverage.data?.items.find(d => JSON.stringify(datasetOnly(d)) === e.target.value) ?? null;
        setDataset(next); setStart(next?.first_candle ?? ''); setEnd(next ? new Date(Date.parse(next.last_candle) + 1).toISOString() : ''); setAsOf(''); analysis.reset();
      }}><option value="">Select dataset</option>{coverage.data?.items.map(d => <option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{d.source} / {d.broker} / {d.symbol} / {d.market_type} / {d.timeframe}</option>)}</select></label>
      <div className="grid compact"><label>Start inclusive (timezone required)<input required value={start} onChange={e => { setStart(e.target.value); analysis.reset(); }} /></label>
        <label>End exclusive (timezone required)<input required value={end} onChange={e => { setEnd(e.target.value); analysis.reset(); }} /></label>
        <label>As-of candle ID (blank = latest)<input type="number" min="0" step="1" value={asOf} onChange={e => { setAsOf(e.target.value); analysis.reset(); }} /></label></div>
      <label className="checkboxLabel"><input type="checkbox" checked={include} onChange={e => { setInclude(e.target.checked); analysis.reset(); }} />Include candle features</label>
      <button type="button" disabled={!def} onClick={() => { setSpecs(def!.defaults.STANDARD.map(s => ({...s}))); analysis.reset(); }}>Load Standard Set</button>
      {specs.map((s, i) => { const d = def?.supported_indicators.find(x => x.type === s.type); return <div className="grid compact" key={i}>
        <label>Indicator {i+1}<select value={s.type} onChange={e => { const next = def!.supported_indicators.find(x => x.type === e.target.value)!; changeSpec(i, { type: next.type, ...next.parameters }); }}>{def?.supported_indicators.map(x => <option key={x.type}>{x.type}</option>)}</select></label>
        <label>Period {i+1}<input type="number" required min={d?.constraints.period.min} max={d?.constraints.period.max} step="1" value={s.period} onChange={e => changeSpec(i, {...s, period: Number(e.target.value)})} /></label>
        {d?.constraints.stddev_multiplier && <label>Multiplier {i+1}<input required type="number" min="0.000001" max={d.constraints.stddev_multiplier.max} step="0.000001" value={s.stddev_multiplier} onChange={e => changeSpec(i, {...s, stddev_multiplier: e.target.value})} /></label>}
        <small>Warmup: {d?.warmup_definition}</small><button type="button" className="secondary" onClick={() => { setSpecs(specs.filter((_, n) => n !== i)); analysis.reset(); }}>Remove {i+1}</button>
      </div>; })}
      <div className="actions"><button type="button" disabled={!def || specs.length >= def.max_indicator_specs} onClick={() => { const d = def!.supported_indicators[0]; setSpecs([...specs, {type: d.type, ...d.parameters}]); analysis.reset(); }}>Add indicator</button>
        <button disabled={!dataset || !def || analysis.isPending}>{analysis.isPending ? 'Analyzing…' : 'Analyze'}</button></div>
    </form>
    {coverage.data && <Paging {...coverage.data} change={n => { setOffset(n); setDataset(null); analysis.reset(); }} />}
    <Failure error={analysis.error} />
  </section>{analysis.data && !analysis.isPending && !analysis.isError && <FeatureResults key={analysis.submittedAt} result={analysis.data} />}</div>;
}
