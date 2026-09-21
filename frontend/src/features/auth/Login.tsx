import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "../../api/auth";
export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const nav = useNavigate();
  const qc = useQueryClient();
  const login = useMutation({
    mutationFn: () => authApi.login(email, password),
    onSuccess: (u) => {
      qc.setQueryData(["me"], u);
      nav("/start");
    },
    onError: (e) => setError((e as Error).message),
  });
  return (
    <div className="auth">
      <div className="authCard">
        <div className="brand">
          CQ<span>•</span>
        </div>
        <div className="eyebrow">ESPACIO DE INVESTIGACIÓN CUANTITATIVA</div>
        <h1>Iniciar sesión</h1>
        <p className="muted">
          Investiga estrategias y lleva un registro de tus operaciones. Sin operaciones automáticas.
        </p>
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            setError("");
            login.mutate();
          }}
        >
          <label>
            Correo electrónico
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error && <div className="state error">{error}</div>}
          <button disabled={login.isPending}>
            {login.isPending ? "Iniciando sesión…" : "Iniciar sesión"}
          </button>
        </form>
      </div>
    </div>
  );
}
