import { codeLabel, datasetLabels } from '../../utils/spanish';
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
    <section className="panel formPanel"><h2>Catálogo de patrones de velas</h2>
      <p>Distribución observada de la vela siguiente. C = vela alcista, P = vela bajista, D = doji exacto. Describen apertura → cierre, no ganancias de operaciones binarias ni señales para operar.</p>
      <p>La frecuencia histórica no demuestra causalidad, independencia, ventaja económica ni rentabilidad futura. Las ventanas superpuestas pueden estar correlacionadas.</p>
      <Failure error={coverage.error} />
      {coverage.isPending && <p>Cargando conjuntos de datos…</p>}
      {coverage.data?.total === 0 && <p>No hay datos disponibles. Un administrador puede importar un CSV.</p>}
      <form onSubmit={e => { e.preventDefault(); if (dataset) analysis.mutate({ ...datasetOnly(dataset), start, end, pattern_length: length, include_doji: doji }); }}>
        <label>Conjunto de datos<select aria-label="Conjunto de datos" required value={dataset ? JSON.stringify(datasetOnly(dataset)) : ""} onChange={e => select(e.target.value)}>
          <option value="">Selecciona un conjunto de datos</option>
          {coverage.data?.items.map(d => <option key={JSON.stringify(datasetOnly(d))} value={JSON.stringify(datasetOnly(d))}>{d.source} / {d.broker} / {d.symbol} / {d.market_type} / {d.timeframe}</option>)}
        </select></label>
        {dataset && <div className="grid compact">{Object.entries(datasetOnly(dataset)).map(([key, value]) => <div key={key}><small>{datasetLabels[key] ?? key}</small><span>{value}</span></div>)}</div>}
        <div className="grid compact">
          <label>Inicio (inclusivo, con zona horaria)<input required value={start} placeholder="2026-09-18T00:00:00Z" onChange={e => setStart(e.target.value)} /></label>
          <label>Fin (exclusivo, con zona horaria)<input required value={end} placeholder="2026-09-20T00:00:00Z" onChange={e => setEnd(e.target.value)} /></label>
          <label>Longitud del patrón<select value={length} onChange={e => setLength(Number(e.target.value))}>{[2, 3, 4, 5].map(n => <option key={n} value={n}>{codeLabel(n)}</option>)}</select></label>
          <label className="checkboxLabel"><input type="checkbox" checked={doji} onChange={e => setDoji(e.target.checked)} />Incluir doji (patrón y resultado)</label>
        </div>
        <button disabled={!dataset || analysis.isPending}>{analysis.isPending ? "Analizando…" : "Analizar"}</button>
      </form>
      {coverage.data && <Paging {...coverage.data} change={n => { setOffset(n); setDataset(null); analysis.reset(); }} />}
      <Failure error={analysis.error} />
    </section>
    {analysis.data && !analysis.isPending && !analysis.isError && <section className="panel" aria-label="Resultados del catálogo">
      <h2>Distribución observada de la vela siguiente</h2><DatasetLabel dataset={analysis.data.metadata} />
      <p>{analysis.data.metadata.start} → {analysis.data.metadata.end} · UTC · longitud {analysis.data.metadata.pattern_length} · doji {analysis.data.metadata.include_doji ? "incluido" : "excluido"}</p>
      <dl className="grid compact">{Object.entries({ "Velas examinadas": analysis.data.candles_examined, "Ventanas aptas": analysis.data.eligible_windows, "Ventanas omitidas por huecos": analysis.data.windows_skipped_due_to_gaps, "Ventanas omitidas por doji": analysis.data.windows_skipped_due_to_doji }).map(([label, n]) => <div key={label}><dt>{label}</dt><dd>{n}</dd></div>)}</dl>
      {analysis.data.patterns.length === 0 && <p>No hay ventanas aptas en este intervalo.</p>}
      <div className="tableWrap"><table><thead><tr>{["Patrón", "Muestras", "Siguiente C", "Siguiente P", "Siguiente D", "C %", "P %", "D %", "Primera observación (UTC)", "Última observación (UTC)", "Días distintos"].map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>
        {analysis.data.patterns.map(p => <tr key={p.pattern}><td>{p.pattern}</td><td>{p.sample_size}{p.sample_size < 30 && <small className="sampleWarning">Muestra pequeña</small>}</td><td>{p.next_bullish_count}</td><td>{p.next_bearish_count}</td><td>{p.next_doji_count}</td><td>{percent(p.next_bullish_probability)}</td><td>{percent(p.next_bearish_probability)}</td><td>{percent(p.next_doji_probability)}</td><td>{p.first_observation}</td><td>{p.last_observation}</td><td>{p.distinct_days}</td></tr>)}
      </tbody></table></div><p>Muestra pequeña: menos de 30 observaciones. Es solo un aviso visual, no un umbral de validez estadística.</p>
    </section>}
  </div>;
}
