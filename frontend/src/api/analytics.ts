import { api } from "./client";
import type { Overview } from "../types";
export const analyticsApi = {
  overview: (accountId: number) =>
    api<Overview>(`/analytics/overview?account_id=${accountId}`),
};
