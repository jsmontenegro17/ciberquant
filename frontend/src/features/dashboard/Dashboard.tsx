import { useAccountSelection } from "../accounts/selection";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { accountsApi } from "../../api/accounts";
import { analyticsApi } from "../../api/analytics";
import { ErrorState } from "../../app/App";
import { money, percent, dateTime } from "../../utils/format";
export function Dashboard() {
  const accounts = useQuery({
    queryKey: ["accounts"],
    queryFn: accountsApi.list,
  });
  const [selected, setSelected] = useAccountSelection();
  const account =
    accounts.data?.find((a) => a.id === Number(selected)) || accounts.data?.[0];
  const overview = useQuery({
    queryKey: ["overview", account?.id],
    queryFn: () => analyticsApi.overview(account!.id),
    enabled: !!account,
  });
  if (accounts.isLoading) return <div className="state">Loading accounts…</div>;
  if (accounts.isError) return <ErrorState />;
  if (!account)
    return (
      <div className="panel">
        <h2>No trading accounts</h2>
        <p className="muted">Create an account to start your workspace.</p>
        <Link className="button" to="/accounts">
          View accounts
        </Link>
      </div>
    );
  if (overview.isLoading) return <div className="state">Loading overview…</div>;
  if (overview.isError) return <ErrorState />;
  const o = overview.data!;
  return (
    <>
      <div className="toolbar">
        <label>
          Trading account
          <select
            value={account.id}
            onChange={(e) => setSelected(e.target.value)}
          >
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} · {a.currency}
              </option>
            ))}
          </select>
        </label>
        <Link
          className="button"
          to={
            o.current_session
              ? `/sessions/${o.current_session.id}`
              : "/sessions/new"
          }
        >
          {o.current_session ? "Continue session" : "Start session"}
        </Link>
      </div>
      <section className="grid">
        {[
          ["Current balance", money(o.current_balance), account.currency],
          ["P&L today", money(o.today_pnl), "Realized"],
          ["Win rate", percent(o.win_rate), "Resolved trades"],
          ["P&L this month", money(o.month_pnl), account.currency],
          ["Operations this month", String(o.monthly_trades), "UTC month"],
          ["Sessions this month", String(o.sessions_count), "UTC month"],
        ].map((c) => (
          <div className="card" key={c[0]}>
            <div className="muted">{c[0]}</div>
            <strong>{c[1]}</strong>
            <small>{c[2]}</small>
          </div>
        ))}
      </section>
      {o.current_session ? (
        <section className="panel">
          <div className="eyebrow">ACTIVE SESSION</div>
          <h2>Session #{o.current_session.id}</h2>
          <p className="muted">
            Started {dateTime(o.current_session.started_at)} ·{" "}
            {o.current_session.max_operations} max operations
          </p>
          <Link to={`/sessions/${o.current_session.id}`} className="button">
            Open workspace
          </Link>
        </section>
      ) : (
        <section className="panel empty">
          <h2>No active session</h2>
          <p className="muted">
            Your account is ready. Start a session when you are ready to record
            evidence.
          </p>
          <Link to="/sessions/new" className="button">
            Start session
          </Link>
        </section>
      )}
      <section className="panel">
        <h2>Recent trades</h2>
        {o.recent_trades?.length ? (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Symbol / market</th>
                  <th>Result</th>
                  <th>P&L</th>
                </tr>
              </thead>
              <tbody>
                {o.recent_trades.map((t) => (
                  <tr key={t.id}>
                    <td>{dateTime(t.opened_at)}</td>
                    <td>
                      {t.symbol} / {t.market_type}
                    </td>
                    <td>{t.result}</td>
                    <td>
                      {money(t.profit_loss)} {account.currency}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>No trades recorded.</p>
        )}
      </section>
    </>
  );
}
