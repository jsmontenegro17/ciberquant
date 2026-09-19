const base =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
export async function api<T>(path: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), init.body instanceof FormData ? 120000 : 30000);
  try {
    const response = await fetch(`${base}${path}`, {
      ...init,
      credentials: "include",
      headers: { ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...(init.headers || {}) },
      signal: controller.signal,
    });
    if (response.status === 401)
      window.dispatchEvent(new Event("cq:unauthorized"));
    if (!response.ok) {
      const body = await response
        .json()
        .catch(() => ({ detail: "Request failed" }));
      throw new Error(
        typeof body.detail === "string"
          ? body.detail
          : Array.isArray(body.detail)
            ? body.detail
                .map((item: { msg?: string }) => item.msg || "Invalid input")
                .join("; ")
            : "Request failed",
      );
    }
    return response.status === 204
      ? (undefined as T)
      : ((await response.json()) as T);
  } finally {
    clearTimeout(timer);
  }
}
