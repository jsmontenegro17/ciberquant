import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { journalApi } from "../../api/journal";
import { ErrorState } from "../../app/App";
import { dateTime } from "../../utils/format";
export function Journal() {
  const q = useQuery({ queryKey: ["journal"], queryFn: journalApi.list });
  const qc = useQueryClient();
  const [content, setContent] = useState("");
  const [session, setSession] = useState("");
  const [trade, setTrade] = useState("");
  const [date, setDate] = useState("");
  const m = useMutation({
    mutationFn: () =>
      journalApi.create({
        title: "Nota de operaciones",
        content,
        session_id: session ? Number(session) : null,
        trade_id: trade ? Number(trade) : null,
      }),
    onSuccess: () => {
      setContent("");
      qc.invalidateQueries({ queryKey: ["journal"] });
    },
  });
  const rows = q.data?.filter(
    (x) =>
      (!session || x.session_id === Number(session)) &&
      (!trade || x.trade_id === Number(trade)) &&
      (!date || new Date(x.created_at).toLocaleDateString("en-CA") === date),
  );
  return (
    <>
      <section className="panel">
        <h2>Diario de operaciones</h2>
        <div className="grid compact">
          <label>
            ID de sesión
            <input
              type="number"
              min="1"
              value={session}
              onChange={(e) => setSession(e.target.value)}
            />
          </label>
          <label>
            ID de operación
            <input
              type="number"
              min="1"
              value={trade}
              onChange={(e) => setTrade(e.target.value)}
            />
          </label>
          <label>
            Fecha
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
        </div>
        <p>Los filtros de sesión y operación también vinculan las notas nuevas a esos registros.</p>
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            if (!m.isPending) m.mutate();
          }}
        >
          <label>
            Nota
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              rows={4}
            />
          </label>
          {m.error && <p role="alert">{m.error.message}</p>}
          <button disabled={m.isPending || !content.trim()}>Añadir nota</button>
        </form>
      </section>
      {q.isLoading ? (
        <p>Cargando diario…</p>
      ) : q.isError ? (
        <ErrorState />
      ) : !rows?.length ? (
        <p>No hay notas del diario para estos filtros.</p>
      ) : (
        rows.map((x) => (
          <article className="panel" key={x.id}>
            <small>{dateTime(x.created_at)}</small>
            <h2>{x.title}</h2>
            <p>{x.content}</p>
            <small>
              {x.session_id ? "Sesión n.º" + x.session_id : "Nota general"}
              {x.trade_id ? " · Operación n.º" + x.trade_id : ""}
            </small>
          </article>
        ))
      )}
    </>
  );
}
