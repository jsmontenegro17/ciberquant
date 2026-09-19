// @vitest-environment jsdom
import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MarketData } from "./MarketData";
import { Cataloger } from "./Cataloger";
import { marketApi, type Coverage, type ImportReport, type CatalogResult } from "../../api/marketData";
vi.mock("../../api/marketData", async importOriginal => ({ ...await importOriginal<typeof import("../../api/marketData")>(), marketApi: { options: vi.fn(), coverage: vi.fn(), imports: vi.fn(), upload: vi.fn(), analyze: vi.fn(), candles: vi.fn() } }));
const dataset: Coverage = { source: "MT5", broker: "BROKERA", symbol: "EURUSD", market_type: "REGULAR", timeframe: "1m", candle_count: 30, first_candle: "2026-09-18T14:00:00Z", last_candle: "2026-09-19T14:14:00Z" };
const report: ImportReport = { ...dataset, id: 1, import_id: 1, status: "COMPLETED", file_name: "fixture.csv", file_sha256: "abc", rows_received: 30, rows_valid: 30, rows_inserted: 30, rows_duplicates: 0, rows_rejected: 0, rows_conflicting: 0, created_at: dataset.first_candle, errors: [], warnings: [] };
const result: CatalogResult = { metadata: { ...dataset, start: dataset.first_candle, end: dataset.last_candle, pattern_length: 3, include_doji: true }, candles_examined: 30, eligible_windows: 24, windows_skipped_due_to_gaps: 3, windows_skipped_due_to_doji: 0, limitation: "Historical only", patterns: [{ pattern: "CCC", pattern_length: 3, sample_size: 6, next_call_count: 0, next_put_count: 6, next_doji_count: 0, next_call_probability: "0", next_put_probability: "1", next_doji_probability: "0", first_observation: dataset.first_candle, last_observation: dataset.last_candle, distinct_days: 2 }] };
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(marketApi.coverage).mockResolvedValue({ items: [dataset], total: 1, offset: 0, limit: 100 });
  vi.mocked(marketApi.imports).mockResolvedValue({ items: [], total: 0, offset: 0, limit: 20 });
  vi.mocked(marketApi.options).mockResolvedValue({ timeframes: ["1m", "5m"], market_types: ["REGULAR", "OTC"], max_upload_mb: 20, max_rows: 100000 });
  vi.mocked(marketApi.upload).mockResolvedValue(report);
  vi.mocked(marketApi.analyze).mockResolvedValue(result);
});
afterEach(cleanup);
function mount(ui: React.ReactNode, role = "USER") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  client.setQueryData(["me"], { id: 1, name: "QA", role });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}
it("renders coverage for USER without administrative import controls", async () => {
  mount(<MarketData />);
  await screen.findByText("BROKERA");
  expect(screen.queryByRole("heading", { name: "Import CSV" })).toBeNull();
  expect(screen.getByText("EURUSD")).toBeTruthy();
});
it("ADMIN confirms metadata and uploads FormData, then sees detailed report", async () => {
  mount(<MarketData />, "ADMIN");
  await screen.findByText(/Maximum 20 MB/);
  fireEvent.change(screen.getByLabelText("Source"), { target: { value: "MT5" } });
  fireEvent.change(screen.getByLabelText("Symbol"), { target: { value: "EURUSD" } });
  const file = new File(["open_time,..."], "fixture.csv", { type: "text/csv" });
  await userEvent.upload(screen.getByLabelText("CSV file"), file);
  // Exercise submit handlers directly; real browser file validity is covered by E2E.
  fireEvent.submit(screen.getByLabelText("CSV file").closest("form")!);
  expect(marketApi.upload).not.toHaveBeenCalled();
  await screen.findByRole("status");
  fireEvent.submit(screen.getByLabelText("CSV file").closest("form")!);
  await screen.findByText("Import COMPLETED");
  const body = vi.mocked(marketApi.upload).mock.calls[0][0];
  expect(body.get("source")).toBe("MT5");
  expect(body.get("file")).toBe(file);
  expect(screen.getByText("Conflicts")).toBeTruthy();
});
it("displays data conflict evidence, not a generic failure", async () => {
  vi.mocked(marketApi.imports).mockResolvedValue({ items: [{ ...report, status: "FAILED", errors: [{ code: "DATA_CONFLICT", message: "Original candle preserved" }] }], total: 1, offset: 0, limit: 20 });
  mount(<MarketData />);
  fireEvent.click(await screen.findByRole("button", { name: "View report #1" }));
  expect(screen.getByRole("alert").textContent).toContain("DATA_CONFLICT");
});
it("catalog analyzes only on request and renders observed results and metadata", async () => {
  mount(<Cataloger />);
  await screen.findByRole("option", { name: /MT5/ });
  expect(marketApi.analyze).not.toHaveBeenCalled();
  const select = screen.getByLabelText("Dataset") as HTMLSelectElement;
  fireEvent.change(select, { target: { value: select.options[1].value } });
  fireEvent.change(screen.getByLabelText("Pattern length"), { target: { value: "4" } });
  fireEvent.click(screen.getByLabelText("Include doji (pattern and outcome)"));
  expect(marketApi.analyze).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
  await screen.findByText("CCC");
  expect(marketApi.analyze).toHaveBeenCalledWith(expect.objectContaining({ broker: "BROKERA", market_type: "REGULAR", pattern_length: 4, include_doji: false }));
  expect(screen.getByText("100.00%")).toBeTruthy();
  expect(screen.getByText("Small sample")).toBeTruthy();
  expect(screen.getByText("Gap windows skipped")).toBeTruthy();
});
it("supports empty dataset state", async () => {
  vi.mocked(marketApi.coverage).mockResolvedValue({ items: [], total: 0, offset: 0, limit: 100 });
  mount(<Cataloger />);
  await screen.findByText("No datasets available. Ask an administrator to import a CSV.");
  expect((screen.getByRole("button", { name: "Analyze" }) as HTMLButtonElement).disabled).toBe(true);
});
it("shows coverage API errors", async () => {
  vi.mocked(marketApi.coverage).mockRejectedValue(new Error("Coverage unavailable"));
  mount(<MarketData />);
  expect((await screen.findByRole("alert")).textContent).toBe("Coverage unavailable");
});
it("shows catalog API errors without previous success results", async () => {
  vi.mocked(marketApi.analyze).mockRejectedValue(new Error("Narrow the date range"));
  mount(<Cataloger />);
  await screen.findByRole("option", { name: /MT5/ });
  const select = screen.getByLabelText("Dataset") as HTMLSelectElement;
  fireEvent.change(select, { target: { value: select.options[1].value } });
  fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Narrow the date range"));
});
it("shows zero eligible windows without invented patterns", async () => {
  vi.mocked(marketApi.analyze).mockResolvedValue({ ...result, patterns: [], eligible_windows: 0 });
  mount(<Cataloger />);
  await screen.findByRole("option", { name: /MT5/ });
  const select = screen.getByLabelText("Dataset") as HTMLSelectElement;
  fireEvent.change(select, { target: { value: select.options[1].value } });
  fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
  await screen.findByText("No eligible windows in this range.");
});
