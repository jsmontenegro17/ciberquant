import { codeLabel } from '../../utils/spanish';
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
  if (q.isLoading) return <p>Cargando sesiones…</p>;
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
        <h2>Historial de sesiones</h2>
        <Link className="button" to="/sessions/new">
          Iniciar sesión de operaciones
        </Link>
      </div>
      <div className="grid compact">
        <label>
          Cuenta
          <select value={account} onChange={(e) => setAccount(e.target.value)}>
            <option value="">Todas las cuentas</option>
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Estado
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos los estados</option>
            <option value={"OPEN"}>{codeLabel("OPEN")}</option>
            <option value={"CLOSED"}>{codeLabel("CLOSED")}</option>
            <option value={"STOPPED"}>{codeLabel("STOPPED")}</option>
          </select>
        </label>
        <label>
          Desde
          <input
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />
        </label>
      </div>
      {!rows?.length ? (
        <p>No hay sesiones para estos filtros.</p>
      ) : (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                {[
                  "Fecha",
                  "Cuenta",
                  "Estado",
                  "Inicial",
                  "Final",
                  "Operaciones",
                  "W",
                  "L",
                  "Porcentaje de aciertos",
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
                  <td>{codeLabel(s.status)}</td>
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
    mutationFn: () =>
      sessionsApi.create({ trading_account_id: Number(account) }),
    onSuccess: (s) => {
      qc.invalidateQueries();
      nav("/sessions/" + s.id);
    },
  });
  return (
    <section className="panel formPanel">
      <h2>Iniciar sesión de operaciones</h2>
      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          if (risk.data && !risk.isError && !create.isPending) create.mutate();
        }}
      >
        <label>
          Cuenta de operaciones
          <select
            required
            value={account}
            onChange={(e) => setAccount(e.target.value)}
          >
            <option value="">Selecciona una cuenta</option>
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} · {a.currency}
              </option>
            ))}
          </select>
        </label>
        {accounts.isLoading && <p>Cargando cuentas…</p>}
        {accounts.isError && <ErrorState />}
        {accounts.data?.length === 0 && (
          <p>No tienes cuentas de operaciones asignadas. Esta pantalla no permite crearlas; la investigación está disponible por separado.</p>
        )}
        {risk.isFetching && account && <p>Cargando perfil de riesgo…</p>}
        {risk.isError && <p role="alert">{risk.error.message}</p>}
        {risk.data && (
          <div className="grid compact">
            {[
              ["Saldo actual", money(risk.data.current_balance)],
              ["Riesgo por operación", percent(risk.data.risk_per_trade_percent)],
              ["Importe sugerido", money(risk.data.suggested_stake)],
              ["Pérdida máxima por sesión", money(risk.data.max_loss_amount)],
              ["Máximo de operaciones", String(risk.data.max_operations)],
              ["Rendimiento mínimo", percent(risk.data.minimum_payout_percent)],
              [
                "Objetivo de ganancia",
                risk.data.profit_target_amount
                  ? money(risk.data.profit_target_amount)
                  : "Sin configurar",
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
        <button disabled={!risk.data || risk.isError || risk.isFetching || create.isPending}>
          {create.isPending ? "Iniciando…" : "Iniciar sesión de operaciones"}
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
    return <div className="state">Cargando sesión…</div>;
  if (!session || summary.isError)
    return <ErrorState message="No se pudo cargar la sesión." />;
  return (
    <>
      <div className="toolbar">
        <div>
          <span className={`status ${session.status.toLowerCase()}`}>
            {codeLabel(session.status)}
          </span>
          <span className="muted">
            {" "}
            · inicio {dateTime(session.started_at)}· Cuenta n.º
            {session.trading_account_id} · {summary.data!.currency}
            {session.ended_at && ` · cierre ${dateTime(session.ended_at)}`}
          </span>
        </div>
        <div className="actions">
          {session.status !== "OPEN" && (
            <button onClick={() => setShowNote(true)}>Añadir nota</button>
          )}
          {session.status === "OPEN" && (
            <>
              <button
                disabled={summary.data!.limit_reached}
                onClick={() => setShowTrade(true)}
              >
                Registrar operación
              </button>
              <button className="secondary" onClick={() => setShowNote(true)}>
                Añadir nota
              </button>
              <Close id={sid} summary={summary.data!} />
            </>
          )}
        </div>
      </div>
      <section className="grid">
        <div className="card">
          <span className="muted">Saldo actual</span>
          <strong>{money(summary.data!.ending_balance)}</strong>
        </div>
        <div className="card">
          <span className="muted">Resultado neto de la sesión</span>
          <strong>{money(summary.data!.net_pnl)}</strong>
        </div>
        <div className="card">
          <span className="muted">Porcentaje de aciertos</span>
          <strong>{percent(summary.data!.win_rate)}</strong>
        </div>
        <div className="card">
          <span className="muted">Operaciones</span>
          <strong>
            {summary.data!.total_trades} / {session.max_operations}
          </strong>
        </div>
      </section>
      <section className="panel">
        <h2>Resumen de sesión</h2>
        <div className="grid compact">
          <div>
            <span>Saldo inicial</span>
            <strong>{money(summary.data!.starting_balance)}</strong>
          </div>
          <div>
            <span>Ganancia bruta</span>
            <strong>{money(summary.data!.gross_profit)}</strong>
          </div>
          <div>
            <span>Pérdida bruta</span>
            <strong>{money(summary.data!.gross_loss)}</strong>
          </div>
          <div>
            <span>Empates / canceladas</span>
            <strong>
              {summary.data!.draws} / {summary.data!.cancelled}
            </strong>
          </div>
        </div>
      </section>
      <section className="panel">
        <div className="panelhead">
          <div>
            <div className="eyebrow">PANEL DE RIESGO</div>
            <h2>Límites de la sesión</h2>
          </div>
          <span className="pill">
            {money(session.max_loss_amount)} pérdida máxima
          </span>
        </div>
        <div className="grid compact">
          <div>
            <span className="muted">Riesgo por operación</span>
            <strong>{percent(session.risk_per_trade_percent)}</strong>
          </div>
          <div>
            <span className="muted">Rendimiento mínimo</span>
            <strong>{percent(session.minimum_payout_percent)}</strong>
          </div>
          <div>
            <span className="muted">Aciertos / pérdidas</span>
            <strong>
              {summary.data!.wins} / {summary.data!.losses}
            </strong>
          </div>
          <div>
            <span className="muted">Rachas</span>
            <strong>
              {summary.data!.max_win_streak}W / {summary.data!.max_loss_streak}L
            </strong>
          </div>
        </div>
      </section>
      {summary.data!.limit_reached && (
        <p role="status">Límite de sesión alcanzado: {summary.data!.limit_reason}</p>
      )}
      <p>
        Importe sugerido: {money(summary.data!.suggested_stake)} · Pérdida acumulada:{" "}
        {money(summary.data!.loss_consumed)} · Riesgo restante:{" "}
        {money(summary.data!.remaining_risk)} · Operaciones restantes:{" "}
        {summary.data!.operations_remaining}
      </p>
      <SessionNotes sid={sid} />
      <TradeList sid={sid} />
      {showTrade &&
        session.status === "OPEN" &&
        !summary.data!.limit_reached && (
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
      <button onClick={() => setConfirming(true)}>Cerrar sesión de operaciones</button>
      {confirming && (
        <section className="panel" aria-label="Confirmar cierre de sesión">
          <p>
            Operaciones: {summary.total_trades} · P&L: {money(summary.net_pnl)} · Saldo: {money(summary.ending_balance)}
          </p>
          {m.error && <p role="alert">{m.error.message}</p>}
          <button disabled={m.isPending} onClick={() => m.mutate()}>
            Confirmar cierre
          </button>
          <button disabled={m.isPending} onClick={() => setConfirming(false)}>
            Cancelar
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
      <div className="eyebrow">OPERACIONES DE LA SESIÓN</div>
      <h2>Operaciones registradas</h2>
      {q.isLoading ? (
        <div className="muted">Cargando operaciones…</div>
      ) : q.isError ? (
        <ErrorState />
      ) : !q.data?.length ? (
        <div className="muted">No hay operaciones registradas.</div>
      ) : (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Hora</th>
                <th>Símbolo</th>
                <th>Mercado</th>
                <th>TF</th>
                <th>Dirección</th>
                <th>Importe</th>
                <th>Rendimiento</th>
                <th>Resultado</th>
                <th>P&L</th>
              </tr>
            </thead>
            <tbody>
              {q.data.map((t, i) => (
                <tr key={t.id}>
                  <td>{i + 1}</td>
                  <td>{dateTime(t.opened_at)}</td>
                  <td>{t.symbol}</td>
                  <td>{codeLabel(t.market_type)}</td>
                  <td>{t.timeframe}</td>
                  <td>{codeLabel(t.direction)}</td>
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
        <h2>Registrar operación</h2>
        <p>Rendimiento mínimo: {percent(session.minimum_payout_percent)}</p>
        {Number(f.payout_percent) < Number(session.minimum_payout_percent) && (
          <p role="alert">El rendimiento es inferior al mínimo.</p>
        )}
        {f.stake !== summary.suggested_stake && (
          <p>El importe difiere del sugerido; se aplican los límites del servidor.</p>
        )}
        <div className="grid compact">
          {[
            ["symbol", "Símbolo"],
            ["timeframe", "Temporalidad"],
            ["stake", "Importe"],
            ["payout_percent", "Rendimiento %"],
            ["opened_at", "Fecha de apertura"],
            ["expiration_at", "Fecha de vencimiento"],
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
            Mercado
            <select
              aria-label="Mercado"
              value={f.market_type}
              onChange={(e) => setF({ ...f, market_type: e.target.value })}
            >
              <option value={"REGULAR"}>{codeLabel("REGULAR")}</option>
              <option value={"OTC"}>{codeLabel("OTC")}</option>
            </select>
          </label>
          <label>
            Dirección
            <select
              aria-label="Dirección"
              value={f.direction}
              onChange={(e) => setF({ ...f, direction: e.target.value })}
            >
              <option value={"CALL"}>{codeLabel("CALL")}</option>
              <option value={"PUT"}>{codeLabel("PUT")}</option>
            </select>
          </label>
          <label>
            Resultado
            <select
              aria-label="Resultado"
              value={f.result}
              onChange={(e) => setF({ ...f, result: e.target.value })}
            >
              <option value={"WIN"}>{codeLabel("WIN")}</option>
              <option value={"LOSS"}>{codeLabel("LOSS")}</option>
              <option value={"DRAW"}>{codeLabel("DRAW")}</option>
              <option value={"CANCELLED"}>{codeLabel("CANCELLED")}</option>
            </select>
          </label>
          <label>
            Notas
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
            Cancelar
          </button>
          <button disabled={m.isPending}>
            {m.isPending ? "Guardando…" : "Guardar operación"}
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
      journalApi.create({ title: "Nota de sesión", content, session_id: sid }),
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
        <h2>Añadir nota al diario</h2>
        {m.error && <p role="alert">{m.error.message}</p>}
        <label>
          Nota
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
            Cancelar
          </button>
          <button disabled={m.isPending}>Guardar nota</button>
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
      <h2>Diario de la sesión</h2>
      {q.isLoading ? (
        <p>Cargando notas…</p>
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
        <p>No hay notas de sesión.</p>
      )}
    </section>
  );
}
