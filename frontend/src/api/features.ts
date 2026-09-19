import { api } from './client';
import type { Dataset } from './marketData';
export interface Spec { type: 'SMA' | 'EMA' | 'RSI' | 'ATR' | 'BOLLINGER'; period: number; stddev_multiplier?: string }
export interface Definition {
  type: Spec['type']; parameters: Omit<Spec, 'type'>;
  constraints: { period: { min: number; max: number }; stddev_multiplier?: { exclusive_min: string; max: string; decimal_places: number } };
  warmup_definition: string; generated_feature_keys: string[];
}
export interface Definitions { calculation_version: string; supported_indicators: Definition[]; defaults: { STANDARD: Spec[] }; max_indicator_specs: number }
export interface ComputeRequest { dataset: Dataset; start: string; end: string; as_of_candle_id: number | null; include_candle_features: boolean; indicators: Spec[] }
export interface FeatureRow {
  candle_id: number; open_time: string; close_time: string; open: string; high: string; low: string; close: string;
  direction: string; gap_before: boolean; gap_seconds: string; contiguous_run_length: number; features: Record<string, string | null>;
}
export interface FeatureResult {
  metadata: { dataset: Dataset; calculation_version: string; as_of_candle_id: number; calculation_anchor: string | null;
    requested_start: string; requested_end: string; candles_processed: number; rows_returned: number };
  feature_keys: string[]; rows: FeatureRow[];
}
export const featureApi = {
  definitions: () => api<Definitions>('/features/definitions'),
  compute: (body: ComputeRequest) => api<FeatureResult>('/features/compute', { method: 'POST', body: JSON.stringify(body) }),
};
