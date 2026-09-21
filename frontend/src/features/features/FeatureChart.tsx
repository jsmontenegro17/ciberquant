import { codeLabel } from '../../utils/spanish';
import { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, LineSeries, createSeriesMarkers, type UTCTimestamp, type Time } from 'lightweight-charts';
import type { FeatureResult, FeatureRow } from '../../api/features';
export const displayValue = (v: string | null | undefined) => v ?? '—';
const time = (r: FeatureRow) => (Date.parse(r.open_time) / 1000) as UTCTimestamp;
export function candleData(rows: FeatureRow[]) {
  return rows.map(r => ({ time: time(r), open: Number(r.open), high: Number(r.high), low: Number(r.low), close: Number(r.close) }));
}
export function lineData(rows: FeatureRow[], key: string) {
  return rows.map(r => r.features[key] == null ? { time: time(r) } : { time: time(r), value: Number(r.features[key]) });
}
export function FeatureChart({ result }: { result: FeatureResult }) {
  const container = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<FeatureRow | null>(null);
  useEffect(() => {
    if (!container.current || result.rows.length === 0) return;
    const chart = createChart(container.current, { autoSize: true, height: 620,
      layout: { attributionLogo: true, background: { color: '#101923' }, textColor: '#cad5df' },
      timeScale: { timeVisible: true, secondsVisible: false },
      localization: { timeFormatter: (t: Time) => new Date(Number(t) * 1000).toISOString() + ' UTC' } });
    const candles = chart.addSeries(CandlestickSeries);
    candles.setData(candleData(result.rows));
    createSeriesMarkers(candles, result.rows.filter(r => r.gap_before).map(r => ({ time: time(r), position: 'aboveBar', shape: 'circle', color: '#eab45c', text: "Hueco de datos" })));
    const hasRsi = result.feature_keys.some(k => k.startsWith('rsi_'));
    const palette = ['#68baff', '#efbd67', '#ba97ff', '#75d4c8'];
    result.feature_keys.filter(k => /^(sma_|ema_|rsi_|atr_|bb_(middle|upper|lower)_)/.test(k)).forEach((key, i) => {
      const rsi = key.startsWith('rsi_'), atr = key.startsWith('atr_');
      const pane = rsi ? 1 : atr ? (hasRsi ? 2 : 1) : 0;
      const line = chart.addSeries(LineSeries, { title: key, color: palette[i % palette.length], lineWidth: 1,
        ...(rsi ? { autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }) } : {}) }, pane);
      line.setData(lineData(result.rows, key));
      if (rsi) [30, 70].forEach(price => line.createPriceLine({ price, color: '#7d8791', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: "Referencia" }));
    });
    chart.panes().forEach((p, i) => p.setStretchFactor(i === 0 ? 3 : 1.5));
    const byTime = new Map(result.rows.map(r => [time(r), r]));
    chart.subscribeCrosshairMove(event => setHover(event.time ? byTime.get(event.time as UTCTimestamp) ?? null : null));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [result]);
  const row = hover ?? result.rows[0];
  return <div>
    <div ref={container} style={{ height: 620 }} aria-label="Gráfico de velas e indicadores" />
    <p>RSI: 0–100; 30/70 son solo referencias visuales. ATR: volatilidad observada. Puntos amarillos: huecos de datos.</p>
    <small>Gráfico de <a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">TradingView Lightweight Charts™</a>. El gráfico usa números del navegador; los valores decimales originales aparecen debajo.</small>
    {row && <div aria-label="Detalle de la vela"><p>{row.open_time} UTC · O {row.open} · H {row.high} · L {row.low} · C {row.close} · {codeLabel(row.direction)} · Hueco {row.gap_before ? row.gap_seconds + 's' : 'no'} · Ejecución {row.contiguous_run_length}</p>
      <div className="grid compact">{result.feature_keys.map(key => <div key={key}><small>{key}</small><span>{displayValue(row.features[key])}</span></div>)}</div></div>}
  </div>;
}
