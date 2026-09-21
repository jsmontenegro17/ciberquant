import { codeLabel } from '../../utils/spanish';
import { useAccountSelection } from "../accounts/selection";
import { StartHint } from '../start/GettingStarted';
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
  if (accounts.isLoading) return <div className="state">Cargando cuentas…</div>;
  if (accounts.isError) return <ErrorState />;
  if (!account)
    return (
      <><StartHint /><div className="panel">
        <h2>No tienes cuentas de operaciones</h2>
        <p className="muted">No necesitas una cuenta de operaciones para investigar estrategias. Consulta la guía de primeros pasos.</p>
        <Link className="button" to="/accounts">
          Ver cuentas
        </Link>
      </div></>
    );
  if (overview.isLoading) return <div className="state">Cargando resumen…</div>;
  if (overview.isError) return <ErrorState />;
  const o = overview.data!;
  return (
    <>
      <StartHint />
      <div className="toolbar">
        <label>
          Cuenta de operaciones
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
          {o.current_session ? "Continuar sesión" : "Iniciar sesión de operaciones"}
        </Link>
      </div>
      <section className="grid">
        {[
          ["Saldo actual", money(o.current_balance), account.currency],
          ["Resultado neto de hoy", money(o.today_pnl), "Realizado"],
          ["Porcentaje de aciertos", percent(o.win_rate), "Operaciones resueltas"],
          ["Resultado neto de este mes", money(o.month_pnl), account.currency],
          ["Operaciones de este mes", String(o.monthly_trades), "Mes UTC"],
          ["Sesiones de este mes", String(o.sessions_count), "Mes UTC"],
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
          <div className="eyebrow">SESIÓN ACTIVA</div>
          <h2>Sesión n.º{o.current_session.id}</h2>
          <p className="muted">
            Inicio {dateTime(o.current_session.started_at)} ·{" "}
            {o.current_session.max_operations} operaciones máximas
          </p>
          <Link to={`/sessions/${o.current_session.id}`} className="button">
            Abrir área de trabajo
          </Link>
        </section>
      ) : (
        <section className="panel empty">
          <h2>No hay una sesión activa</h2>
          <p className="muted">
            Tu cuenta está lista. Inicia una sesión cuando quieras registrar tus operaciones manualmente.
          </p>
          <Link to="/sessions/new" className="button">
            Iniciar sesión de operaciones
          </Link>
        </section>
      )}
      <section className="panel">
        <h2>Operaciones recientes</h2>
        {o.recent_trades?.length ? (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Hora</th>
                  <th>Símbolo / mercado</th>
                  <th>Resultado</th>
                  <th>P&L</th>
                </tr>
              </thead>
              <tbody>
                {o.recent_trades.map((t) => (
                  <tr key={t.id}>
                    <td>{dateTime(t.opened_at)}</td>
                    <td>
                      {t.symbol} / {codeLabel(t.market_type)}
                    </td>
                    <td>{codeLabel(t.result)}</td>
                    <td>
                      {money(t.profit_loss)} {account.currency}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>No hay operaciones registradas.</p>
        )}
      </section>
    </>
  );
}
