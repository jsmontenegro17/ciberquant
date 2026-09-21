// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FeatureLab } from './FeatureLab';
import { candleData, lineData, displayValue } from './FeatureChart';
import { featureApi, type Definitions, type FeatureResult } from '../../api/features';
import { marketApi, datasetOnly, type Coverage } from '../../api/marketData';
const chart = vi.hoisted(() => ({ setData: vi.fn(), addSeries: vi.fn(), remove: vi.fn(), markers: vi.fn() }));
vi.mock('lightweight-charts', () => ({ CandlestickSeries: 'candles', LineSeries: 'line', createSeriesMarkers: chart.markers,
  createChart: () => ({ addSeries: chart.addSeries, panes: () => [], subscribeCrosshairMove: vi.fn(), timeScale: () => ({ fitContent: vi.fn() }), remove: chart.remove }) }));
vi.mock('../../api/features', () => ({ featureApi: { definitions: vi.fn(), compute: vi.fn() } }));
vi.mock('../../api/marketData', async original => ({ ...await original<typeof import('../../api/marketData')>(), marketApi: { coverage: vi.fn() } }));
const dataset: Coverage = { source: 'FIXTURE', broker: 'DEMO', symbol: 'EURUSD', market_type: 'REGULAR', timeframe: '1m', candle_count: 1, first_candle: '2026-01-01T00:00:00Z', last_candle: '2026-01-01T00:00:00Z' };
const definitions: Definitions = { calculation_version: 'cq-features-v1', max_indicator_specs: 12,
  supported_indicators: ['SMA','EMA','RSI','ATR','BOLLINGER'].map(type => ({ type: type as 'SMA', parameters: { period: 20, ...(type === 'BOLLINGER' ? {stddev_multiplier:'2'} : {}) }, constraints: { period: {min:2, max:500}, ...(type === 'BOLLINGER' ? {stddev_multiplier:{exclusive_min:'0',max:'10',decimal_places:6}} : {}) }, warmup_definition: 'period candles', generated_feature_keys: [] })),
  defaults: { STANDARD: [{type:'EMA',period:9},{type:'EMA',period:20},{type:'EMA',period:50},{type:'RSI',period:14},{type:'ATR',period:14},{type:'BOLLINGER',period:20,stddev_multiplier:'2'}] } };
const result: FeatureResult = { metadata: {dataset,calculation_version:'cq-features-v1',as_of_candle_id:42,calculation_anchor:dataset.first_candle,requested_start:dataset.first_candle,requested_end:'2026-01-02T00:00:00Z',candles_processed:1,rows_returned:1},feature_keys:['ema_20','rsi_14','atr_14'],
  rows:[{candle_id:42,open_time:dataset.first_candle,close_time:'2026-01-01T00:01:00Z',open:'1',high:'2',low:'1',close:'2',direction:'C',gap_before:true,gap_seconds:'60',contiguous_run_length:1,features:{ema_20:null,rsi_14:'0',atr_14:'1'}}] };
beforeEach(() => {
  vi.resetAllMocks();
  chart.addSeries.mockReturnValue({ setData: chart.setData, createPriceLine: vi.fn() });
  vi.mocked(featureApi.definitions).mockResolvedValue(definitions);
  vi.mocked(featureApi.compute).mockResolvedValue(result);
  vi.mocked(marketApi.coverage).mockResolvedValue({items:[dataset],total:1,offset:0,limit:100});
});
afterEach(cleanup);
async function mount() {
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><FeatureLab /></QueryClientProvider>);
  await screen.findByRole('option', {name:'FIXTURE / DEMO / EURUSD / REGULAR / 1m'});
  fireEvent.change(screen.getByLabelText("Conjunto de datos"), {target:{value:JSON.stringify(datasetOnly(dataset))}});
}
it('loads definitions and preset; explicit compute feeds actual rows to chart and renders snapshot/null versus zero', async () => {
  await mount();
  fireEvent.click(screen.getByText("Cargar conjunto estándar"));
  expect(screen.getByLabelText("Período 6")).toBeTruthy();
  expect(featureApi.compute).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', {name:"Analizar"}));
  await screen.findByText('cq-features-v1');
  expect(vi.mocked(featureApi.compute).mock.calls[0][0].indicators).toEqual(definitions.defaults.STANDARD);
  expect(screen.getByText("ID de vela de corte")).toBeTruthy();
  expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  expect(screen.getAllByText('0').length).toBeGreaterThan(0);
  expect(chart.setData).toHaveBeenCalledWith(candleData(result.rows));
  expect(chart.addSeries.mock.calls.map(c => c[2])).toContain(2);
  expect(chart.markers).toHaveBeenCalledWith(expect.anything(), [expect.objectContaining({text:"Hueco de datos"})]);
});
it('custom parameters and snapshot are sent; removal updates specs', async () => {
  await mount();
  fireEvent.click(screen.getByText("Añadir indicador"));
  fireEvent.change(screen.getByLabelText("Indicador 1"), {target:{value:'BOLLINGER'}});
  fireEvent.change(screen.getByLabelText("Período 1"), {target:{value:'5'}});
  fireEvent.change(screen.getByLabelText("Multiplicador 1"), {target:{value:'2.5'}});
  fireEvent.change(screen.getByLabelText("ID de vela de corte (vacío = última)"), {target:{value:'42'}});
  fireEvent.click(screen.getByRole('button', {name:"Analizar"}));
  await waitFor(() => expect(featureApi.compute).toHaveBeenCalled());
  expect(vi.mocked(featureApi.compute).mock.calls[0][0]).toMatchObject({as_of_candle_id:42, indicators:[{type:'BOLLINGER',period:5,stddev_multiplier:'2.5'}]});
  fireEvent.click(screen.getByText("Quitar 1"));
  expect(screen.queryByLabelText("Período 1")).toBeNull();
});
it('exposes API rejection without showing stale results', async () => {
  vi.mocked(featureApi.compute).mockRejectedValue(new Error('Exact origin calculation exceeds cap'));
  await mount();
  fireEvent.click(screen.getByRole('button', {name:"Analizar"}));
  expect((await screen.findByRole('alert')).textContent).toContain('exceeds cap');
  expect(screen.queryByRole('region', {name:"Resultados de indicadores"})).toBeNull();
});
it('preserves whitespace warmups and legitimate zero when adapting API data', () => {
  expect(lineData(result.rows,'ema_20')).toEqual([{time:1767225600}]);
  expect(lineData(result.rows,'rsi_14')).toEqual([{time:1767225600,value:0}]);
  expect(displayValue(null)).toBe('—'); expect(displayValue('0')).toBe('0');
});
