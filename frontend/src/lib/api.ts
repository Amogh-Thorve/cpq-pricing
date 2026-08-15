/**
 * CPQ Platform API Client
 *
 * A thin, typed wrapper around the browser Fetch API.
 * All domain hooks import from this module — never call fetch() directly in components.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface APIError {
  detail: string;
  error_code: string;
  details?: Record<string, unknown> | null;
}

// ─── Token storage ────────────────────────────────────────────────────────────

export const tokenStorage = {
  get: (): string | null =>
    typeof window !== "undefined" ? localStorage.getItem("cpq_access_token") : null,
  set: (token: string) =>
    typeof window !== "undefined" && localStorage.setItem("cpq_access_token", token),
  clear: () =>
    typeof window !== "undefined" && localStorage.removeItem("cpq_access_token"),
};

// ─── Core request helper ──────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = tokenStorage.get();

  const headers: Record<string, string> = {
    ...(!(options.body instanceof FormData) && { "Content-Type": "application/json" }),
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error: APIError = await response.json().catch(() => ({
      detail: "An unexpected error occurred.",
      error_code: "UNKNOWN_ERROR",
    }));
    throw error;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// ─── API Methods ──────────────────────────────────────────────────────────────

export const api = {
  get: <T>(path: string) =>
    request<T>(path, { method: "GET" }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),

  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),

  upload: <T>(path: string, body: FormData) =>
    request<T>(path, { method: "POST", body }),

  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
};
