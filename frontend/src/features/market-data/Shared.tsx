import type { Dataset } from "../../api/marketData";

export function DatasetLabel({ dataset }: { dataset: Dataset }) {
  return <span>{dataset.source} / {dataset.broker} / {dataset.symbol} / {dataset.market_type} / {dataset.timeframe}</span>;
}
export function Paging({ offset, limit, total, change }: { offset: number; limit: number; total: number; change: (n: number) => void }) {
  return <div className="actions">
    <button className="secondary" disabled={offset === 0} onClick={() => change(Math.max(0, offset - limit))}>Previous</button>
    <span>{total === 0 ? 0 : offset + 1}–{Math.min(total, offset + limit)} of {total}</span>
    <button className="secondary" disabled={offset + limit >= total} onClick={() => change(offset + limit)}>Next</button>
  </div>;
}
export function Failure({ error }: { error: Error | null }) {
  return error ? <p role="alert" className="state error">{error.message}</p> : null;
}

