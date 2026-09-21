import { codeLabel } from '../../utils/spanish';
import { useQuery } from "@tanstack/react-query";
import { accountsApi } from "../../api/accounts";
import { money } from "../../utils/format";
import { ErrorState } from "../../app/App";
export function Accounts() {
  const q = useQuery({ queryKey: ["accounts"], queryFn: accountsApi.list });
  if (q.isLoading) return <div className="state">Cargando cuentas…</div>;
  if (q.isError) return <ErrorState />;
  if (!q.data?.length)
    return (
      <div className="panel empty">
        <h2>Sin cuentas</h2>
        <p className="muted">
          No tienes cuentas de operaciones asignadas. Esta versión permite consultarlas, pero no crearlas desde esta pantalla.
        </p>
      </div>
    );
  return (
    <div className="stack">
      {q.data.map((a) => (
        <section className="panel" key={a.id}>
          <div className="panelhead">
            <div>
              <div className="eyebrow">CUENTA DE OPERACIONES</div>
              <h2>{a.name}</h2>
            </div>
            <span className="pill">{codeLabel(a.status)}</span>
          </div>
          <div className="grid compact">
            <div>
              <span className="muted">Bróker</span>
              <strong>{a.broker || "—"}</strong>
            </div>
            <div>
              <span className="muted">Saldo inicial</span>
              <strong>
                {money(a.initial_balance)} {a.currency}
              </strong>
            </div>
            <div>
              <span className="muted">Saldo actual</span>
              <strong>
                {money(a.current_balance)} {a.currency}
              </strong>
            </div>
          </div>
          <Ledger id={a.id} />
        </section>
      ))}
    </div>
  );
}
function Ledger({ id }: { id: number }) {
  const q = useQuery({
    queryKey: ["ledger", id],
    queryFn: () => accountsApi.ledger(id),
  });
  return (
    <div className="tableWrap">
      <h3>Movimientos de saldo</h3>
      {q.isLoading ? (
        <div className="muted">Cargando movimientos…</div>
      ) : q.isError ? (
        <ErrorState />
      ) : !q.data?.length ? (
        <div className="muted">No hay movimientos registrados.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Importe</th>
              <th>Saldo posterior</th>
            </tr>
          </thead>
          <tbody>
            {q.data.map((x) => (
              <tr key={x.id}>
                <td>{codeLabel(x.entry_type)}</td>
                <td>{money(x.amount)}</td>
                <td>{money(x.balance_after)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
