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
import { StrategyLab, StrategyDetail } from "../features/research/StrategyLab";
import { Backtests, BacktestResult } from "../features/research/Backtests";
import {ValidationList,ValidationSetup,ValidationDetail} from '../features/validation/Validation';
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
            <Route path="/strategies" element={<StrategyLab />} />
            <Route path="/strategies/:id" element={<StrategyDetail />} />
            <Route path="/backtests" element={<Backtests />} />
            <Route path="/backtests/:id" element={<BacktestResult />} />
            <Route path="/validation" element={<ValidationList />} />
            <Route path="/validation/new" element={<ValidationSetup />} />
            <Route path="/validation/:id" element={<ValidationDetail />} />
            {["settings"].map(
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
