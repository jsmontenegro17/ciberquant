import {useEffect, useState} from 'react';
import {
  Navigate,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi } from "../api/auth";
import type { User } from "../types";
export function Protected() {
  const navigate=useNavigate();
  const cache=useQueryClient();
  useEffect(()=>{
    const expired=()=>{cache.clear();navigate('/login',{replace:true})};
    window.addEventListener('cq:unauthorized',expired);
    return ()=>window.removeEventListener('cq:unauthorized',expired);
  },[cache,navigate]);
  const q = useQuery<User>({
    queryKey: ["me"],
    queryFn: authApi.me,
    retry: false,
  });
  if (q.isLoading) return <div className="center">Cargando área de trabajo…</div>;
  if (q.isError) return <Navigate to="/login" replace />;
  return <Outlet />;
}
export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const nav = useNavigate();
  const qc = useQueryClient();
  const user = qc.getQueryData<User>(["me"]);
  const logout = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      qc.clear();
      nav("/login");
    },
  });
  return (
    <div className="app">
      <aside>
        <div className="brand">
          CQ<span>•</span>
        </div>
        <div className="muted">INVESTIGACIÓN</div>
        <button className="menuToggle secondary" aria-expanded={menuOpen} aria-controls="main-navigation" onClick={()=>setMenuOpen(!menuOpen)}>{menuOpen ? 'Ocultar menú' : 'Abrir menú'}</button>
        <nav id="main-navigation" aria-label="Navegación principal" className={`navLinks ${menuOpen ? 'isOpen' : ''}`}>
        {[
          ["Primeros pasos", "/start"],
          ["Resumen", "/dashboard"],
          ["Área de investigación", "/workspace"],
          ["Cuentas", "/accounts"],
          ["Sesiones", "/sessions"],
          ["Diario", "/journal"],
          ["Datos de mercado", "/market-data"],
          ["Patrones de velas", "/cataloger"],
          ["Indicadores", "/features"],
          ["Estrategias", "/strategies"],
          ["Pruebas históricas", "/backtests"],
          ["Validación", "/validation"],
          ["Seguimiento en vivo", "/scanner"],
        ].map(([x, p]) => (
          <NavLink
            className={({ isActive }) => `nav ${isActive ? "active" : ""}`}
            to={p}
            key={p}
            onClick={()=>setMenuOpen(false)}
          >
            {x}
          </NavLink>
        ))}
        </nav>
        <div className="bottom">
          <div className="user">
            ◉ {user?.name}
            <br />
            <small>{user?.email}</small>
          </div>
          <button className="linkButton" onClick={() => logout.mutate()}>
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main>
        <header>
          <div>
            <div className="eyebrow">CIBERQUANT / ÁREA DE TRABAJO</div>
            <h1>{pageTitles[useLocation().pathname.split("/")[1]] ?? 'CiberQuant'}</h1>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
const pageTitles: Record<string,string> = {
  start:'Primeros pasos', dashboard:'Resumen', workspace:'Área de investigación',
  accounts:'Cuentas', sessions:'Sesiones', journal:'Diario', 'market-data':'Datos de mercado',
  cataloger:'Patrones de velas', features:'Indicadores', strategies:'Estrategias',
  backtests:'Pruebas históricas', validation:'Validación', scanner:'Seguimiento en vivo', settings:'Configuración',
};
export function ErrorState({
  message = "No se pudieron cargar los datos.",
}: {
  message?: string;
}) {
  return (
    <div className="state error">
      {message}
      <button onClick={() => location.reload()}>Reintentar</button>
    </div>
  );
}
