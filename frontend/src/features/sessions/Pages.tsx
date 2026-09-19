import { useAccountSelection } from "../accounts/selection";
import { riskPreview } from "../../api/risk";
import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { accountsApi } from "../../api/accounts";
import { sessionsApi } from "../../api/sessions";
import { tradesApi } from "../../api/trades";
import { journalApi } from "../../api/journal";
import { ErrorState } from "../../app/App";
import { money, percent, dateTime } from "../../utils/format";
import type { Session, Summary } from "../../types";
export function Sessions() {
  const q = useQuery({ queryKey: ["sessions"], queryFn: sessionsApi.list });
  const accounts = useQuery({
    queryKey: ["accounts"],
    queryFn: accountsApi.list,
  });
  const [account, setAccount] = useAccountSelection();
  const [status, setStatus] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  if (q.isLoading) return <p>Loading sessions…</p>;
  if (q.isError) return <ErrorState />;
  const rows = q.data?.filter(
    (s) =>
      (!account || s.trading_account_id === Number(account)) &&
      (!status || s.status === status) &&
      (!from || s.started_at.slice(0, 10) >= from) &&
      (!to || s.started_at.slice(0, 10) <= to),
  );
  return (
    <>
      <div className="toolbar">
        <h2>Session history</h2>
        <Link className="button" to="/sessions/new">
          Start session
        </Link>
      </div>
      <div className="grid compact">
        <label>
          Account
          <select value={account} onChange={(e) => setAccount(e.target.value)}>
            <option value="">All accounts</option>
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option>OPEN</option>
            <option>CLOSED</option>
            <option>STOPPED</option>
          </select>
        </label>
        <label>
          From
          <input
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />
        </label>
      </div>
      {!rows?.length ? (
        <p>No sessions for these filters.</p>
      ) : (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                {[
                  "Date",
                  "Account",
                  "Status",
                  "Starting",
                  "Ending",
                  "Trades",
                  "W",
                  "L",
                  "Win rate",
                  "P&L",
                ].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td>
                    <Link to={"/sessions/" + s.id}>
                      {dateTime(s.started_at)}
                    </Link>
                  </td>
                  <td>
                    {accounts.data?.find((a) => a.id === s.trading_account_id)
                      ?.name || s.trading_account_id}{" "}
                    · {s.currency}
                  </td>
                  <td>{s.status}</td>
                  <td>{money(s.starting_balance)}</td>
                  <td>{money(s.ending_balance)}</td>
                  <td>{s.total_trades}</td>
                  <td>{s.wins}</td>
                  <td>{s.losses}</td>
                  <td>{percent(s.win_rate)}</td>
                  <td>{money(s.net_pnl)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
export function NewSession() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const [account, setAccount] = useAccountSelection();
  const accounts = useQuery({
    queryKey: ["accounts"],
    queryFn: accountsApi.list,
  });
  const risk = useQuery({
    queryKey: ["risk", account],
    queryFn: () => riskPreview(Number(account)),
    enabled: !!account,
  });
  const create = useMutation({
    mutationFn: () => sessionsApi.create(risk.data!),
    onSuccess: (s) => {
      qc.invalidateQueries();
      nav("/sessions/" + s.id);
    },
  });
  return (
    <section className="panel formPanel">
      <h2>Start session</h2>
      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          if (risk.data && !create.isPending) create.mutate();
        }}
      >
        <label>
          Trading account
          <select
            required
            value={account}
            onChange={(e) => setAccount(e.target.value)}
          >
            <option value="">Select account</option>
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} · {a.currency}
              </option>
            ))}
          </select>
        </label>
        {accounts.isLoading && <p>Loading accounts…</p>}
        {accounts.isError && <ErrorState />}
        {accounts.data?.length === 0 && (
          <p>No accounts. Create one from Accounts.</p>
        )}
        {risk.isFetching && account && <p>Loading risk profile…</p>}
        {risk.isError && <p role="alert">{risk.error.message}</p>}
        {risk.data && (
          <div className="grid compact">
            {[
              ["Current balance", money(risk.data.current_balance)],
              ["Risk per trade", percent(risk.data.risk_per_trade_percent)],
              ["Suggested stake", money(risk.data.suggested_stake)],
              ["Max session loss", money(risk.data.max_loss_amount)],
              ["Max operations", String(risk.data.max_operations)],
              ["Minimum payout", percent(risk.data.minimum_payout_percent)],
              [
                "Profit target",
                risk.data.profit_target_amount
                  ? money(risk.data.profit_target_amount)
                  : "Not configured",
              ],
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        )}
        {create.error && <p role="alert">{create.error.message}</p>}
        <button disabled={!risk.data || risk.isFetching || create.isPending}>
          {create.isPending ? "Starting…" : "Start session"}
        </button>
      </form>
    </section>
  );
}
export function SessionWorkspace() {
  const { id } = useParams();
  const sid = Number(id);
  const qc = useQueryClient();
  const s = useQuery({ queryKey: ["sessions"], queryFn: sessionsApi.list });
  const summary = useQuery({
    queryKey: ["summary", sid],
    queryFn: () => sessionsApi.summary(sid),
  });
  const session = s.data?.find((x) => x.id === sid);
  const [showTrade, setShowTrade] = useState(false);
  const [showNote, setShowNote] = useState(false);
  if (s.isLoading || summary.isLoading)
    return <div className="state">Loading session…</div>;
  if (!session || summary.isError)
    return <ErrorState message="Could not load session." />;
  return (
    <>
      <div className="toolbar">
        <div>
          <span className={`status ${session.status.toLowerCase()}`}>
            {session.status}
          </span>
          <span className="muted">
            {" "}
            · started {dateTime(session.started_at)}
            · Account #{session.trading_account_id} · {summary.data!.currency}
            {session.ended_at && ` · closed ${dateTime(session.ended_at)}`}
          </span>
        </div>
        <div className="actions">
          {session.status !== "OPEN" && <button onClick={() => setShowNote(true)}>Add note</button>}
          {session.status === "OPEN" && (
            <>
              <button
                disabled={summary.data!.limit_reached}
                onClick={() => setShowTrade(true)}
              >
                Record trade
              </button>
              <button className="secondary" onClick={() => setShowNote(true)}>
                Add note
              </button>
              <Close id={sid} summary={summary.data!} />
            </>
          )}
        </div>
      </div>
      <section className="grid">
        <div className="card">
          <span className="muted">Current balance</span>
          <strong>{money(summary.data!.ending_balance)}</strong>
        </div>
        <div className="card">
          <span className="muted">Session P&L</span>
          <strong>{money(summary.data!.net_pnl)}</strong>
        </div>
        <div className="card">
          <span className="muted">Win rate</span>
          <strong>{percent(summary.data!.win_rate)}</strong>
        </div>
        <div className="card">
          <span className="muted">Operations</span>
          <strong>
            {summary.data!.total_trades} / {session.max_operations}
          </strong>
        </div>
      </section>
      <section className="panel">
        <h2>Session summary</h2>
        <div className="grid compact">
          <div><span>Starting balance</span><strong>{money(summary.data!.starting_balance)}</strong></div>
          <div><span>Gross profit</span><strong>{money(summary.data!.gross_profit)}</strong></div>
          <div><span>Gross loss</span><strong>{money(summary.data!.gross_loss)}</strong></div>
          <div><span>Draws / cancelled</span><strong>{summary.data!.draws} / {summary.data!.cancelled}</strong></div>
        </div>
      </section>
      <section className="panel">
        <div className="panelhead">
          <div>
            <div className="eyebrow">RISK PANEL</div>
            <h2>Session guardrails</h2>
          </div>
          <span className="pill">
            {money(session.max_loss_amount)} max loss
          </span>
        </div>
        <div className="grid compact">
          <div>
            <span className="muted">Risk per trade</span>
            <strong>{percent(session.risk_per_trade_percent)}</strong>
          </div>
          <div>
            <span className="muted">Minimum payout</span>
            <strong>{percent(session.minimum_payout_percent)}</strong>
          </div>
          <div>
            <span className="muted">Wins / losses</span>
            <strong>
              {summary.data!.wins} / {summary.data!.losses}
            </strong>
          </div>
          <div>
            <span className="muted">Streaks</span>
            <strong>
              {summary.data!.max_win_streak}W / {summary.data!.max_loss_streak}L
            </strong>
          </div>
        </div>
      </section>
      {summary.data!.limit_reached && (
        <p role="status">Session limit reached: {summary.data!.limit_reason}</p>
      )}
      <p>
        Suggested stake: {money(summary.data!.suggested_stake)} · Loss consumed:{" "}
        {money(summary.data!.loss_consumed)} · Remaining risk:{" "}
        {money(summary.data!.remaining_risk)} · Operations remaining:{" "}
        {summary.data!.operations_remaining}
      </p>
      <SessionNotes sid={sid} />
      <TradeList sid={sid} />
      {showTrade && session.status === "OPEN" && !summary.data!.limit_reached && (
        <TradeForm
          summary={summary.data!}
          session={session}
          onDone={() => {
            setShowTrade(false);
            qc.invalidateQueries({ queryKey: ["summary", sid] });
            qc.invalidateQueries({ queryKey: ["sessions"] });
          }}
        />
      )}
      {showNote && <NoteForm sid={sid} onDone={() => setShowNote(false)} />}
    </>
  );
}
export function Close({ id, summary }: { id: number; summary: Summary }) {
  const [confirming, setConfirming] = useState(false);
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: () => sessionsApi.close(id),
    onSuccess: () => {
      qc.invalidateQueries();
      setConfirming(false);
    },
  });
  return (
    <div>
      <button onClick={() => setConfirming(true)}>Close session</button>
      {confirming && (
        <section className="panel" aria-label="Confirm closure">
          <p>
            Trades: {summary.total_trades} · P&L: {money(summary.net_pnl)} ·
            Balance: {money(summary.ending_balance)}
          </p>
          {m.error && <p role="alert">{m.error.message}</p>}
          <button disabled={m.isPending} onClick={() => m.mutate()}>
            Confirm close
          </button>
          <button disabled={m.isPending} onClick={() => setConfirming(false)}>
            Cancel
          </button>
        </section>
      )}
    </div>
  );
}
function TradeList({ sid }: { sid: number }) {
  const q = useQuery({
    queryKey: ["trades", sid],
    queryFn: () => sessionsApi.trades(sid),
  });
  return (
    <div className="panel">
      <div className="eyebrow">SESSION TRADES</div>
      <h2>Recorded operations</h2>
      {q.isLoading ? (
        <div className="muted">Loading trades…</div>
      ) : q.isError ? <ErrorState/> : !q.data?.length ? (
        <div className="muted">No trades recorded.</div>
      ) : (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Time</th>
                <th>Symbol</th>
                <th>Market</th>
                <th>TF</th>
                <th>Direction</th>
                <th>Stake</th>
                <th>Payout</th>
                <th>Result</th>
                <th>P&L</th>
              </tr>
            </thead>
            <tbody>
              {q.data.map((t, i) => (
                <tr key={t.id}>
                  <td>{i + 1}</td>
                  <td>{dateTime(t.opened_at)}</td>
                  <td>{t.symbol}</td>
                  <td>{t.market_type}</td>
                  <td>{t.timeframe}</td>
                  <td>{t.direction}</td>
                  <td>{money(t.stake)}</td>
                  <td>{percent(t.payout_percent)}</td>
                  <td>{t.result || "OPEN"}</td>
                  <td>{money(t.profit_loss)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
export function TradeForm({
  session,
  summary,
  onDone,
}: {
  session: Session;
  summary: Summary;
  onDone: () => void;
}) {
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: (body: object) => tradesApi.create(body),
    onSuccess: () => {
      qc.invalidateQueries();
      onDone();
    },
  });
  const [f, setF] = useState({
    symbol: "",
    market_type: "REGULAR",
    timeframe: "1m",
    direction: "CALL",
    stake: summary.suggested_stake,
    payout_percent: session.minimum_payout_percent,
    result: "WIN",
    opened_at: "",
    expiration_at: "",
    notes: "",
  });
  return (
    <section className="panel">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          m.mutate({
            ...f,
            opened_at: f.opened_at
              ? new Date(f.opened_at).toISOString()
              : new Date().toISOString(),
            expiration_at: f.expiration_at
              ? new Date(f.expiration_at).toISOString()
              : null,
            trading_account_id: session.trading_account_id,
            trading_session_id: session.id,
          });
        }}
      >
        <h2>Record trade</h2>
        <p>Minimum payout: {percent(session.minimum_payout_percent)}</p>
        {Number(f.payout_percent) < Number(session.minimum_payout_percent) && (
          <p role="alert">Payout is below the minimum.</p>
        )}
        {f.stake !== summary.suggested_stake && (
          <p>Stake differs from the recommendation; backend limits apply.</p>
        )}
        <div className="grid compact">
          {[
            ["symbol", "Symbol"],
            ["timeframe", "Timeframe"],
            ["stake", "Stake"],
            ["payout_percent", "Payout %"],
            ["opened_at", "Opened at"],
            ["expiration_at", "Expiration at"],
          ].map(([k, l]) => (
            <label key={k}>
              {l}
              <input
                autoFocus={k === "symbol"}
                required={k !== "expiration_at"}
                type={
                  k.endsWith("_at")
                    ? "datetime-local"
                    : k === "stake" || k === "payout_percent"
                      ? "number"
                      : "text"
                }
                step="any"
                min={k === "stake" ? "0.01" : "0"}
                value={f[k as keyof typeof f]}
                onChange={(e) => setF({ ...f, [k]: e.target.value })}
              />
            </label>
          ))}
          <label>
            Market
            <select
              aria-label="Market"
              value={f.market_type}
              onChange={(e) => setF({ ...f, market_type: e.target.value })}
            >
              <option>REGULAR</option>
              <option>OTC</option>
            </select>
          </label>
          <label>
            Direction
            <select
              aria-label="Direction"
              value={f.direction}
              onChange={(e) => setF({ ...f, direction: e.target.value })}
            >
              <option>CALL</option>
              <option>PUT</option>
            </select>
          </label>
          <label>
            Result
            <select
              aria-label="Result"
              value={f.result}
              onChange={(e) => setF({ ...f, result: e.target.value })}
            >
              <option>WIN</option>
              <option>LOSS</option>
              <option>DRAW</option>
              <option>CANCELLED</option>
            </select>
          </label>
          <label>
            Notes
            <textarea
              value={f.notes}
              onChange={(e) => setF({ ...f, notes: e.target.value })}
            />
          </label>
        </div>
        {m.error && (
          <div className="state error">{(m.error as Error).message}</div>
        )}
        <div className="actions">
          <button type="button" className="secondary" onClick={onDone}>
            Cancel
          </button>
          <button disabled={m.isPending}>
            {m.isPending ? "Saving…" : "Save trade"}
          </button>
        </div>
      </form>
    </section>
  );
}
export function NoteForm({ sid, onDone }: { sid: number; onDone: () => void }) {
  const qc = useQueryClient();
  const [content, setContent] = useState("");
  const m = useMutation({
    mutationFn: () =>
      journalApi.create({ title: "Session note", content, session_id: sid }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["journal"] });
      onDone();
    },
  });
  return (
    <section className="panel">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          m.mutate();
        }}
      >
        <h2>Add journal note</h2>
        {m.error && <p role="alert">{m.error.message}</p>}
        <label>
          Note
          <textarea
            autoFocus
            id="note"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            rows={5}
          />
        </label>
        <div className="actions">
          <button type="button" className="secondary" onClick={onDone}>
            Cancel
          </button>
          <button disabled={m.isPending}>Save note</button>
        </div>
      </form>
    </section>
  );
}
function SessionNotes({ sid }: { sid: number }) {
  const q = useQuery({ queryKey: ["journal"], queryFn: journalApi.list });
  const notes = q.data?.filter((n) => n.session_id === sid);
  return (
    <section className="panel">
      <h2>Session journal</h2>
      {q.isLoading ? (
        <p>Loading notes…</p>
      ) : q.isError ? (
        <ErrorState />
      ) : notes?.length ? (
        notes.map((n) => (
          <article key={n.id}>
            <small>{dateTime(n.created_at)}</small>
            <p>{n.content}</p>
          </article>
        ))
      ) : (
        <p>No session notes.</p>
      )}
    </section>
  );
}
