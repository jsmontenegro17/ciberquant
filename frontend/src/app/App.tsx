import {useEffect} from 'react';
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
  if (q.isLoading) return <div className="center">Loading workspace…</div>;
  if (q.isError) return <Navigate to="/login" replace />;
  return <Outlet />;
}
export function Layout() {
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
        <div className="muted">RESEARCH DESK</div>
        {[
          ["Dashboard", "/dashboard"],
          ["Accounts", "/accounts"],
          ["Sessions", "/sessions"],
          ["Journal", "/journal"],
          ["Market Data", "/market-data"],
          ["Cataloger", "/cataloger"],
          ["Feature Lab", "/features"],
          ["Strategy Lab", "/strategies"],
          ["Backtests", "/backtests"],
          ["Validation", "/validation"],
          ["Scanner", "/scanner"],
        ].map(([x, p]) => (
          <NavLink
            className={({ isActive }) => `nav ${isActive ? "active" : ""}`}
            to={p}
            key={p}
          >
            {x}
          </NavLink>
        ))}
        <div className="bottom">
          <div className="user">
            ◉ {user?.name}
            <br />
            <small>{user?.email}</small>
          </div>
          <button className="linkButton" onClick={() => logout.mutate()}>
            Sign out
          </button>
        </div>
      </aside>
      <main>
        <header>
          <div>
            <div className="eyebrow">CIBERQUANT / WORKSPACE</div>
            <h1>{useLocation().pathname.split("/")[1] || "dashboard"}</h1>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
export function ErrorState({
  message = "Could not load data.",
}: {
  message?: string;
}) {
  return (
    <div className="state error">
      {message}
      <button onClick={() => location.reload()}>Retry</button>
    </div>
  );
}
