// @vitest-environment jsdom
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  render,
  screen,
  waitFor,
  fireEvent,
  act,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import {
  NewSession,
  TradeForm,
  SessionWorkspace,
  NoteForm,
  Close,
} from "./Pages";
import { Protected } from "../../app/App";
import { authApi } from "../../api/auth";
import { accountsApi } from "../../api/accounts";
import { sessionsApi } from "../../api/sessions";
import { tradesApi } from "../../api/trades";
import { journalApi } from "../../api/journal";
import { riskPreview } from "../../api/risk";
import type { Session, Summary } from "../../types";
vi.mock("../../api/auth");
vi.mock("../../api/accounts");
vi.mock("../../api/sessions");
vi.mock("../../api/trades");
vi.mock("../../api/journal");
vi.mock("../../api/risk");
const session: Session = {
  id: 7,
  user_id: 1,
  trading_account_id: 3,
  starting_balance: "2000",
  status: "OPEN",
  started_at: "2026-09-19T10:00:00Z",
  risk_per_trade_percent: "1",
  max_loss_amount: "40",
  max_operations: 4,
  minimum_payout_percent: "80",
};
const summary: Summary = {
  session_id: 7,
  total_trades: 1,
  wins: 1,
  losses: 0,
  draws: 0,
  cancelled: 0,
  win_rate: "100",
  gross_profit: "16.8",
  gross_loss: "0",
  net_pnl: "16.8",
  starting_balance: "2000",
  ending_balance: "2016.8",
  max_win_streak: 1,
  max_loss_streak: 0,
  currency: "USD",
  suggested_stake: "20.17",
  loss_consumed: "0",
  remaining_risk: "40",
  operations_remaining: 3,
  limit_reached: false,
  limit_reason: null,
};
function mount(component: React.ReactNode, path = "/") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>{component}</MemoryRouter>
    </QueryClientProvider>,
  );
  return client;
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(sessionsApi.list).mockResolvedValue([session]);
  vi.mocked(sessionsApi.summary).mockResolvedValue(summary);
  vi.mocked(sessionsApi.trades).mockResolvedValue([]);
  vi.mocked(journalApi.list).mockResolvedValue([]);
});
afterEach(cleanup);
describe("REQ-002 user workflow", () => {
  it("Guardar operación label disappears while mutation is pending, before form completion", async () => {
    let release!: (value: Awaited<ReturnType<typeof tradesApi.create>>) => void;
    vi.mocked(tradesApi.create).mockImplementation(() => new Promise(resolve => { release = resolve; }));
    const done = vi.fn();
    mount(<TradeForm session={session} summary={summary} onDone={done}/>);
    fireEvent.change(screen.getByLabelText("Símbolo"),{target:{value:'EURUSD'}});
    fireEvent.change(screen.getByLabelText("Fecha de apertura"),{target:{value:'2026-09-19T10:00'}});
    fireEvent.click(screen.getByRole('button',{name:"Guardar operación"}));
    await screen.findByRole('button',{name:"Guardando…"});
    expect(screen.queryByRole('button',{name:"Guardar operación"})).toBeNull();
    expect(screen.getByRole('heading',{name:"Registrar operación"})).toBeTruthy();
    expect(done).not.toHaveBeenCalled();
    await act(async()=>release({} as Awaited<ReturnType<typeof tradesApi.create>>));
    await waitFor(()=>expect(done).toHaveBeenCalledOnce());
  });
  it("disables start when no risk profile is configured", async () => {
    vi.mocked(accountsApi.list).mockResolvedValue([
      {
        id: 3,
        name: "No profile",
        currency: "USD",
        initial_balance: "2000",
        current_balance: "2000",
        status: "ACTIVE",
      },
    ]);
    vi.mocked(riskPreview).mockRejectedValue(
      new Error("No risk profile configured"),
    );
    const cache=mount(<NewSession />);
    // A previously valid preview must not allow a start after the profile disappears.
    cache.setQueryData(['risk','3'],{trading_account_id:3,current_balance:'2000',currency:'USD',risk_per_trade_percent:'1',suggested_stake:'20',max_loss_amount:'40',max_operations:4,minimum_payout_percent:'80',profit_target_amount:null});
    await screen.findByText("No profile · USD");
    fireEvent.change(screen.getByLabelText("Cuenta de operaciones"), {
      target: { value: "3" },
    });
    await screen.findByText("No risk profile configured");
    expect(
      (
        screen.getByRole("button", {
          name: "Iniciar sesión de operaciones",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(sessionsApi.create).not.toHaveBeenCalled();
  });
  it("renders backend net loss and remaining risk", async () => {
    vi.mocked(sessionsApi.summary).mockResolvedValue({
      ...summary,
      net_pnl: "-3.37",
      loss_consumed: "3.37",
      remaining_risk: "36.63",
    });
    mount(
      <Routes>
        <Route path="/sessions/:id" element={<SessionWorkspace />} />
      </Routes>,
      "/sessions/7",
    );
    await screen.findByText(/Pérdida acumulada: 3[.,]37/);
    expect(screen.getByText(/Riesgo restante: 36[.,]63/)).toBeTruthy();
  });
  it("redirects an unauthenticated protected route", async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error("Unauthorized"));
    mount(
      <Routes>
        <Route element={<Protected />}>
          <Route path="/" element={<p>Private</p>} />
        </Route>
        <Route path="/login" element={<p>Sign in required</p>} />
      </Routes>,
    );
    await screen.findByText("Sign in required");
    expect(screen.queryByText("Private")).toBeNull();
  });
  it("starts a session from backend risk values", async () => {
    vi.mocked(accountsApi.list).mockResolvedValue([
      {
        id: 3,
        name: "Research account",
        currency: "EUR",
        initial_balance: "750",
        current_balance: "750",
        status: "ACTIVE",
      },
    ]);
    vi.mocked(riskPreview).mockResolvedValue({
      trading_account_id: 3,
      current_balance: "750",
      currency: "EUR",
      risk_per_trade_percent: "2",
      suggested_stake: "15",
      max_loss_amount: "30",
      max_operations: 2,
      minimum_payout_percent: "83",
      profit_target_amount: null,
    });
    vi.mocked(sessionsApi.create).mockResolvedValue(session);
    mount(
      <Routes>
        <Route path="/" element={<NewSession />} />
        <Route path="/sessions/7" element={<p>Workspace ready</p>} />
      </Routes>,
    );
    await screen.findByText("Research account · EUR");
    fireEvent.change(screen.getByLabelText("Cuenta de operaciones"), {
      target: { value: "3" },
    });
    await screen.findByText(/15[.,]00/);
    fireEvent.click(screen.getByRole("button", { name: "Iniciar sesión de operaciones" }));
    await screen.findByText("Workspace ready");
    expect(sessionsApi.create).toHaveBeenCalledWith({ trading_account_id: 3 });
  });
  it("submits a trade with the recommended stake and shows backend rejection", async () => {
    vi.mocked(tradesApi.create).mockRejectedValue(
      new Error("Importe exceeds per-trade risk limit"),
    );
    mount(<TradeForm session={session} summary={summary} onDone={() => {}} />);
    expect((screen.getByLabelText("Importe") as HTMLInputElement).value).toBe(
      "20.17",
    );
    fireEvent.change(screen.getByLabelText("Símbolo"), {
      target: { value: "EURUSD" },
    });
    fireEvent.change(screen.getByLabelText("Fecha de apertura"), {
      target: { value: "2026-09-19T10:00" },
    });
    fireEvent.change(screen.getByLabelText("Importe"), {
      target: { value: "20.18" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar operación" }));
    await screen.findByText("Importe exceeds per-trade risk limit");
    expect(tradesApi.create).toHaveBeenCalledWith(
      expect.objectContaining({
        stake: "20.18",
        trading_session_id: 7,
        result: "WIN",
      }),
    );
  });
  it("blocks recording when backend reports session limit", async () => {
    vi.mocked(sessionsApi.summary).mockResolvedValue({
      ...summary,
      limit_reached: true,
      limit_reason: "Máximo operations reached",
      operations_remaining: 0,
    });
    mount(
      <Routes>
        <Route path="/sessions/:id" element={<SessionWorkspace />} />
      </Routes>,
      "/sessions/7",
    );
    await screen.findByText(/Límite de sesión alcanzado/);
    expect(
      (
        screen.getByRole("button", {
          name: "Registrar operación",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });
  it("requires confirmation to close and persists the closed UI", async () => {
    vi.mocked(sessionsApi.close).mockImplementation(async () => {
      vi.mocked(sessionsApi.list).mockResolvedValue([
        { ...session, status: "CLOSED" },
      ]);
      return { ...session, status: "CLOSED" };
    });
    mount(
      <Routes>
        <Route path="/sessions/:id" element={<SessionWorkspace />} />
      </Routes>,
      "/sessions/7",
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Cerrar sesión de operaciones" }),
    );
    expect(sessionsApi.close).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cierre" }));
    await screen.findByText("Cerrada (CLOSED)");
    expect(screen.queryByRole("button", { name: "Registrar operación" })).toBeNull();
  });
  it("saves a session note and refreshes the journal cache", async () => {
    const done = vi.fn();
    vi.mocked(journalApi.create).mockResolvedValue({
      id: 1,
      user_id: 1,
      title: "Nota de sesión",
      content: "Waited for confirmation",
      session_id: 7,
      created_at: "2026-09-19T10:00:00Z",
    });
    const cache = mount(<NoteForm sid={7} onDone={done} />);
    const invalidate = vi.spyOn(cache, "invalidateQueries");
    fireEvent.change(screen.getByLabelText("Nota"), {
      target: { value: "Waited for confirmation" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar nota" }));
    await waitFor(() => expect(done).toHaveBeenCalledOnce());
    expect(journalApi.create).toHaveBeenCalledWith(
      expect.objectContaining({
        session_id: 7,
        content: "Waited for confirmation",
      }),
    );
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["journal"] });
  });
});
