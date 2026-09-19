import { api } from "./client";
import type { User } from "../types";
export const authApi = {
  login: (email: string, password: string) =>
    api<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => api("/auth/logout", { method: "POST" }),
  me: () => api<User>("/auth/me"),
};
