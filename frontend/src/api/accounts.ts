import { api } from "./client";
import type { Account, Ledger } from "../types";
export const accountsApi = {
  list: () => api<Account[]>("/accounts"),
  ledger: (id: number) => api<Ledger[]>(`/accounts/${id}/ledger`),
};
