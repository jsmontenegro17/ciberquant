import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { datasetOnly, marketApi, type Coverage, type CatalogFilter } from "../../api/marketData";
import { DatasetLabel, Failure, Paging } from "./Shared";

const percent = (value: string) => (Number(value) * 100).toFixed(2) + "%";
export function Cataloger() {
  const [offset, setOffset] = useState(0);
  const coverage = useQuery({ queryKey: ["coverage", offset], queryFn: () => marketApi.coverage(offset) });
  const [dataset, setDataset] = useState<Coverage | null>(null);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [length, setLength] = useState(3);
  const [doji, setDoji] = useState(true);
  const analysis = useMutation({ mutationFn: (filter: CatalogFilter) => marketApi.analyze(filter) });
  const select = (value: string) => {
    const next = coverage.data?.items.find(d => JSON.stringify(datasetOnly(d)) === value) || null;
    setDataset(next); analysis.reset();
    setStart(next?.first_candle || "");
    setEnd(next ? new Date(new Date(next.last_candle).getTime() + 1).toISOString() : "");
  };
  return <div>
    <section className="panel formPanel"><h2>Candle Cataloger</h2>
      <p>Observed next-candle distribution. C = bullish, P = bearish, D = exact doji. These are candle colors, not trading signals.</p>
      <p>Historical frequency does not establish causality, independence, economic advantage or future profitability. Overlapping windows may be autocorrelated.</p>
      <Failure error={coverage.error} />
      {coverage.isPending && <p>Loading datasets…</p>}
      {coverage.data?.total === 0 && <p>No datasets available. Ask an administrator to import a CSV.</p>}
      <form onSubmit={e => { e.preventDefault(); if (dataset) analysis.mutate({ ...datasetOnly(dataset), start, end, pattern_length: length, include_doji: doji }); }}>
        <label>Dataset<select aria-label="Dataset" required value={dataset ? JSON.stringify(datasetOnly(dataset)) : ""} onChange={e => select(e.target.value)}>
          <option value="">Select dataset</option>
          {coverage.data?.items.map(d => <option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{d.source} / {d.broker} / {d.symbol} / {d.market_type} / {d.timeframe}</option>)}
        </select></label>
        {dataset && <div className="grid compact">{Object.entries(datasetOnly(dataset)).map(([key, value]) => <div key={key}><small>{key}</small><span>{value}</span></div>)}</div>}
        <div className="grid compact">
          <label>Start (inclusive, timezone required)<input required value={start} placeholder="2026-09-18T00:00:00Z" onChange={e => setStart(e.target.value)} /></label>
          <label>End (exclusive, timezone required)<input required value={end} placeholder="2026-09-20T00:00:00Z" onChange={e => setEnd(e.target.value)} /></label>
          <label>Pattern length<select value={length} onChange={e => setLength(Number(e.target.value))}>{[2, 3, 4, 5].map(n => <option key={n}>{n}</option>)}</select></label>
          <label className="checkboxLabel"><input type="checkbox" checked={doji} onChange={e => setDoji(e.target.checked)} />Include doji (pattern and outcome)</label>
        </div>
        <button disabled={!dataset || analysis.isPending}>{analysis.isPending ? "Analyzing…" : "Analyze"}</button>
      </form>
      {coverage.data && <Paging {...coverage.data} change={n => { setOffset(n); setDataset(null); analysis.reset(); }} />}
      <Failure error={analysis.error} />
    </section>
    {analysis.data && !analysis.isPending && !analysis.isError && <section className="panel" aria-label="Catalog results">
      <h2>Observed next-candle distribution</h2><DatasetLabel dataset={analysis.data.metadata} />
      <p>{analysis.data.metadata.start} → {analysis.data.metadata.end} · UTC · length {analysis.data.metadata.pattern_length} · doji {analysis.data.metadata.include_doji ? "included" : "excluded"}</p>
      <dl className="grid compact">{Object.entries({ "Candles examined": analysis.data.candles_examined, "Eligible windows": analysis.data.eligible_windows, "Gap windows skipped": analysis.data.windows_skipped_due_to_gaps, "Doji windows skipped": analysis.data.windows_skipped_due_to_doji }).map(([label, n]) => <div key={label}><dt>{label}</dt><dd>{n}</dd></div>)}</dl>
      {analysis.data.patterns.length === 0 && <p>No eligible windows in this range.</p>}
      <div className="tableWrap"><table><thead><tr>{["Pattern", "Samples", "Next C", "Next P", "Next D", "C %", "P %", "D %", "First observation (UTC)", "Last observation (UTC)", "Distinct days"].map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>
        {analysis.data.patterns.map(p => <tr key={p.pattern}><td>{p.pattern}</td><td>{p.sample_size}{p.sample_size < 30 && <small className="sampleWarning">Small sample</small>}</td><td>{p.next_call_count}</td><td>{p.next_put_count}</td><td>{p.next_doji_count}</td><td>{percent(p.next_call_probability)}</td><td>{percent(p.next_put_probability)}</td><td>{percent(p.next_doji_probability)}</td><td>{p.first_observation}</td><td>{p.last_observation}</td><td>{p.distinct_days}</td></tr>)}
      </tbody></table></div><p>Small sample: fewer than 30 observations; a display reminder only, not a statistical validity threshold.</p>
    </section>}
  </div>;
}
