import { useQuery } from "@tanstack/react-query";
import { accountsApi } from "../../api/accounts";
import { money } from "../../utils/format";
import { ErrorState } from "../../app/App";
export function Accounts() {
  const q = useQuery({ queryKey: ["accounts"], queryFn: accountsApi.list });
  if (q.isLoading) return <div className="state">Loading accounts…</div>;
  if (q.isError) return <ErrorState />;
  if (!q.data?.length)
    return (
      <div className="panel empty">
        <h2>No accounts</h2>
        <p className="muted">
          There are no trading accounts available for this user.
        </p>
      </div>
    );
  return (
    <div className="stack">
      {q.data.map((a) => (
        <section className="panel" key={a.id}>
          <div className="panelhead">
            <div>
              <div className="eyebrow">TRADING ACCOUNT</div>
              <h2>{a.name}</h2>
            </div>
            <span className="pill">{a.status}</span>
          </div>
          <div className="grid compact">
            <div>
              <span className="muted">Broker</span>
              <strong>{a.broker || "—"}</strong>
            </div>
            <div>
              <span className="muted">Initial balance</span>
              <strong>
                {money(a.initial_balance)} {a.currency}
              </strong>
            </div>
            <div>
              <span className="muted">Current balance</span>
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
      <h3>Ledger</h3>
      {q.isLoading ? (
        <div className="muted">Loading ledger…</div>
      ) : q.isError ? (
        <ErrorState />
      ) : !q.data?.length ? (
        <div className="muted">No movements recorded.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Amount</th>
              <th>Balance after</th>
            </tr>
          </thead>
          <tbody>
            {q.data.map((x) => (
              <tr key={x.id}>
                <td>{x.entry_type}</td>
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
