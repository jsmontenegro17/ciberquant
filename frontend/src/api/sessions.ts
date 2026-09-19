import { api } from "./client";
import type { Session, Summary, Trade } from "../types";
export const sessionsApi = {
  list: () => api<Session[]>("/sessions"),
  create: (body: { trading_account_id: number; notes?: string }) =>
    api<Session>("/sessions", { method: "POST", body: JSON.stringify(body) }),
  close: (id: number) =>
    api<Session>(`/sessions/${id}/close`, { method: "POST" }),
  summary: (id: number) => api<Summary>(`/sessions/${id}/summary`),
  trades: (id: number) => api<Trade[]>(`/sessions/${id}/trades`),
};
