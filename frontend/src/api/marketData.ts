import { api } from "./client";

export interface Dataset {
  source: string; broker: string; symbol: string; market_type: string; timeframe: string;
}
export interface Coverage extends Dataset { candle_count: number; first_candle: string; last_candle: string }
export interface Page<T> { items: T[]; total: number; offset: number; limit: number }
export interface Issue { code: string; row?: number; message: string }
export interface ImportReport extends Dataset {
  id: number; import_id: number; status: string; file_name: string; file_sha256: string;
  rows_received: number; rows_valid: number; rows_inserted: number; rows_duplicates: number;
  rows_rejected: number; rows_conflicting: number; created_at: string; errors: Issue[]; warnings: Issue[];
}
export interface Candle extends Dataset {
  id: number; import_id: number | null; open_time: string; close_time: string;
  open: string; high: string; low: string; close: string; tick_volume: string | null; spread: string | null;
}
export interface CatalogFilter extends Dataset { start: string; end: string; pattern_length: number; include_doji: boolean }
export interface Pattern {
  pattern: string; pattern_length: number; sample_size: number;
  next_bullish_count: number; next_bearish_count: number; next_doji_count: number;
  next_bullish_probability: string; next_bearish_probability: string; next_doji_probability: string;
  first_observation: string; last_observation: string; distinct_days: number;
}
export interface CatalogResult {
  metadata: CatalogFilter; candles_examined: number; eligible_windows: number;
  windows_skipped_due_to_gaps: number; windows_skipped_due_to_doji: number;
  patterns: Pattern[]; limitation: string;
}
export function datasetOnly(d: Dataset): Dataset {
  return { source: d.source, broker: d.broker, symbol: d.symbol, market_type: d.market_type, timeframe: d.timeframe };
}
export function params(values: object) {
  return new URLSearchParams(Object.entries(values).map(([k, v]) => [k, String(v)])).toString();
}
export const marketApi = {
  options: () => api<{ timeframes: string[]; market_types: string[]; max_upload_mb: number; max_rows: number }>("/market-data/options"),
  coverage: (offset = 0) => api<Page<Coverage>>("/market-data/coverage?" + params({ offset, limit: 100 })),
  imports: (offset = 0) => api<Page<ImportReport>>("/market-data/imports?" + params({ offset, limit: 20 })),
  upload: (body: FormData) => api<ImportReport>("/market-data/imports/csv", { method: "POST", body }),
  candles: (dataset: Coverage, offset = 0) => api<Page<Candle>>("/market-data/candles?" + params({
    ...datasetOnly(dataset), start: dataset.first_candle,
    end: new Date(new Date(dataset.last_candle).getTime() + 1).toISOString(), offset, limit: 20
  })),
  analyze: (filters: CatalogFilter) => api<CatalogResult>("/cataloger/patterns?" + params(filters)),
};
