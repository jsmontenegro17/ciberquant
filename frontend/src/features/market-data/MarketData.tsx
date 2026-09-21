import { codeLabel } from '../../utils/spanish';
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { marketApi, type Coverage, type ImportReport } from "../../api/marketData";
import type { User } from "../../types";
import { DatasetLabel, Failure, Paging } from "./Shared";

export function Report({ report }: { report: ImportReport }) {
  return <section className="panel" aria-label="Informe de importación">
    <h2>Importación {codeLabel(report.status)}</h2>
    <DatasetLabel dataset={report} />
    <p>{report.file_name} · Lote n.º{report.import_id}</p>
    <dl className="grid compact">
      {Object.entries({ "Filas recibidas": report.rows_received, "Válidas": report.rows_valid, "Insertadas": report.rows_inserted, "Duplicadas": report.rows_duplicates, "Rechazadas": report.rows_rejected, "Conflictos": report.rows_conflicting }).map(([label, count]) =>
        <div key={label}><dt>{label}</dt><dd>{count}</dd></div>)}
    </dl>
    {report.errors.length > 0 && <div role="alert"><h3>Errores</h3><ul>{report.errors.map((e, i) => <li key={i}>{e.code}{e.row ? " · fila " + e.row : ""}: {e.message}</li>)}</ul></div>}
    {report.warnings.length > 0 && <><h3>Advertencias</h3><ul>{report.warnings.map((w, i) => <li key={i}>{w.code}: {w.message}</li>)}</ul></>}
    <small>SHA-256: {report.file_sha256}</small>
  </section>;
}
export function ImportForm() {
  const qc = useQueryClient();
  const options = useQuery({ queryKey: ["market-options"], queryFn: marketApi.options });
  const [file, setFile] = useState<File | null>(null);
  const [meta, setMeta] = useState({ source: "", broker: "UNSPECIFIED", symbol: "", market_type: "REGULAR", timeframe: "1m" });
  const [confirm, setConfirm] = useState(false);
  const upload = useMutation({
    mutationFn: marketApi.upload,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["coverage"] }); qc.invalidateQueries({ queryKey: ["imports"] }); qc.invalidateQueries({ queryKey: ["candles"] }); setConfirm(false); },
  });
  const update = (key: string, value: string) => { setMeta({ ...meta, [key]: value }); setConfirm(false); };
  return <section className="panel formPanel">
    <h2>Importar CSV</h2>
    <p>Un archivo corresponde a un conjunto de datos. Las fechas deben incluir zona horaria; las velas originales no se pueden editar. No se conservan los archivos subidos.</p>
    <Failure error={options.error} />
    {options.data && <p>Máximo {options.data.max_upload_mb} MB / {options.data.max_rows.toLocaleString()} filas.</p>}
    <form onSubmit={e => {
      e.preventDefault();
      if (!file) return;
      if (!confirm) { setConfirm(true); return; }
      const body = new FormData();
      Object.entries(meta).forEach(([key, value]) => body.append(key, value));
      body.append("file", file);
      upload.mutate(body);
    }}>
      <div className="grid compact">
        {(["source", "broker", "symbol"] as const).map(key => <label key={key}>{key === "symbol" ? "Símbolo" : key === "source" ? "Fuente" : "Bróker"}
          <input required value={meta[key]} maxLength={key === "broker" ? 120 : 50} onChange={e => update(key, e.target.value)} /></label>)}
        <label>Tipo de mercado<select value={meta.market_type} onChange={e => update("market_type", e.target.value)}>{options.data?.market_types.map(v => <option key={v} value={v}>{codeLabel(v)}</option>)}</select></label>
        <label>Temporalidad<select value={meta.timeframe} onChange={e => update("timeframe", e.target.value)}>{options.data?.timeframes.map(v => <option key={v} value={v}>{codeLabel(v)}</option>)}</select></label>
      </div>
      <label>Archivo CSV<input type="file" accept=".csv,text/csv" required onChange={e => { setFile(e.target.files?.[0] || null); setConfirm(false); }} /></label>
      {confirm && file && <div className="riskPreview" role="status">
        <b>Revisar importación</b><span>{file.name} · {file.size.toLocaleString()} bytes</span>
        <DatasetLabel dataset={meta} />
        <span>Confirma estos metadatos antes de importar.</span>
      </div>}
      <button disabled={upload.isPending || !options.data || !file}>{upload.isPending ? "Importando…" : confirm ? "Confirmar importación" : "Revisar importación"}</button>
      <Failure error={upload.error} />
      {upload.isError && <p>La solicitud puede haber llegado al servidor. Revisa el historial antes de reintentar; los duplicados exactos se pueden reimportar sin duplicar velas.</p>}
    </form>
    {upload.data && <Report report={upload.data} />}
  </section>;
}
function Inspection({ dataset }: { dataset: Coverage }) {
  const [offset, setOffset] = useState(0);
  const q = useQuery({ queryKey: ["candles", dataset, offset], queryFn: () => marketApi.candles(dataset, offset) });
  return <section className="panel"><h2>Inspección de velas</h2><DatasetLabel dataset={dataset} /><Failure error={q.error} />
    {q.isPending && <p>Cargando velas…</p>}
    <div className="tableWrap"><table><thead><tr>{["Hora de apertura (UTC)", "Hora de cierre (UTC)", "Apertura", "Máximo", "Mínimo", "Cierre", "Volumen", "Diferencial de precios", "Importación"].map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>
      {q.data?.items.map(c => <tr key={c.id}><td>{c.open_time}</td><td>{c.close_time}</td><td>{c.open}</td><td>{c.high}</td><td>{c.low}</td><td>{c.close}</td><td>{c.tick_volume ?? "—"}</td><td>{c.spread ?? "—"}</td><td>{c.import_id ?? "Histórico anterior"}</td></tr>)}
    </tbody></table></div>
    {q.data && <Paging {...q.data} change={setOffset} />}
  </section>;
}
export function MarketData() {
  const qc = useQueryClient();
  const user = qc.getQueryData<User>(["me"]);
  const [offset, setOffset] = useState(0);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [selected, setSelected] = useState<Coverage | null>(null);
  const [report, setReport] = useState<ImportReport | null>(null);
  const coverage = useQuery({ queryKey: ["coverage", offset], queryFn: () => marketApi.coverage(offset) });
  const history = useQuery({ queryKey: ["imports", historyOffset], queryFn: () => marketApi.imports(historyOffset) });
  return <div>
    <section className="panel"><h2>Cobertura de datos</h2><p>Observaciones históricas inmutables · UTC</p>
      <Failure error={coverage.error} />
      {coverage.isPending && <p>Cargando conjuntos de datos…</p>}
      {coverage.data?.total === 0 && <p>Todavía no hay conjuntos de datos importados.</p>}
      <div className="tableWrap"><table><thead><tr>{["Fuente", "Bróker", "Activo", "Mercado", "TF", "Velas", "Desde", "Hasta", "Inspeccionar"].map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>
        {coverage.data?.items.map(d => <tr key={[d.source, d.broker, d.symbol, d.market_type, d.timeframe].join("|")}>
          <td>{d.source}</td><td>{d.broker}</td><td>{d.symbol}</td><td>{d.market_type}</td><td>{d.timeframe}</td><td>{d.candle_count}</td><td>{d.first_candle}</td><td>{d.last_candle}</td><td><button onClick={() => setSelected(d)}>Inspeccionar</button></td>
        </tr>)}
      </tbody></table></div>
      {coverage.data && <Paging {...coverage.data} change={setOffset} />}
    </section>
    {selected && <Inspection key={JSON.stringify(selected)} dataset={selected} />}
    {user?.role === "ADMIN" && <ImportForm />}
    <section className="panel"><h2>Historial de importaciones</h2><Failure error={history.error} />
      {history.data?.total === 0 && <p>Todavía no hay importaciones.</p>}
      <div className="tableWrap"><table><thead><tr>{["Fecha", "Conjunto de datos", "Archivo", "Filas", "Estado", "Informe"].map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>
        {history.data?.items.map(item => <tr key={item.id}><td>{item.created_at}</td><td><DatasetLabel dataset={item} /></td><td>{item.file_name}</td><td>{item.rows_received}</td><td>{codeLabel(item.status)}</td><td><button onClick={() => setReport(item)}>Ver informe n.º{item.id}</button></td></tr>)}
      </tbody></table></div>
      {history.data && <Paging {...history.data} change={setHistoryOffset} />}
    </section>
    {report && <Report report={report} />}
  </div>;
}

