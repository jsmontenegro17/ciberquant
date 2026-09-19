import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout, Protected } from "./App";
import { Login } from "../features/auth/Login";
import { Dashboard } from "../features/dashboard/Dashboard";
import { Accounts } from "../features/accounts/Accounts";
import {
  Sessions,
  NewSession,
  SessionWorkspace,
} from "../features/sessions/Pages";
import { Journal } from "../features/journal/Journal";
import { MarketData } from "../features/market-data/MarketData";
import { Cataloger } from "../features/market-data/Cataloger";
import { FeatureLab } from "../features/features/FeatureLab";
export function Router() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<Protected />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/sessions" element={<Sessions />} />
            <Route path="/sessions/new" element={<NewSession />} />
            <Route path="/sessions/:id" element={<SessionWorkspace />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/market-data" element={<MarketData />} />
            <Route path="/cataloger" element={<Cataloger />} />
            <Route path="/features" element={<FeatureLab />} />
            {["settings", "strategies", "backtests"].map(
              (path) => (
                <Route
                  key={path}
                  path={"/" + path}
                  element={
                    <section className="panel">
                      <h2>{path}</h2>
                      <p>Planned for a future requirement.</p>
                    </section>
                  }
                />
              ),
            )}
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
