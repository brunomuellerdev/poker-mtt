import { useAuthStore } from "@/stores/authStore";

const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

// Single-flight refresh: concurrent 401s share one refresh call.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include", // send httpOnly refresh cookie
      });
      if (!res.ok) return null;
      const data = (await res.json()) as { access_token: string };
      useAuthStore.getState().setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  retry?: boolean;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    }
  }
  return url.pathname + url.search;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, retry = true } = opts;
  const token = useAuthStore.getState().accessToken;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(buildUrl(path, query), {
    method,
    headers,
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // try a one-time refresh on auth failure, then replay the request
  if (res.status === 401 && retry) {
    const newToken = await refreshAccessToken();
    if (newToken) return request<T>(path, { ...opts, retry: false });
    useAuthStore.getState().clear();
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiError(res.status, parseDetail(data) || res.statusText);
  }
  return data as T;
}

interface ValidationItem {
  loc?: (string | number)[];
  msg?: string;
}

// FastAPI returns `detail` as a string for business errors, or an array of
// {loc, msg, ...} objects for 422 validation errors. Flatten both to a string.
function parseDetail(data: unknown): string {
  if (!data || typeof data !== "object" || !("detail" in data)) {
    return "Request failed";
  }
  const detail = (data as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return (detail as ValidationItem[])
      .map((e) => {
        const field = e.loc?.filter((p) => p !== "body").join(".") ?? "";
        return field ? `${field}: ${e.msg}` : (e.msg ?? "invalid");
      })
      .join("; ");
  }
  return "Request failed";
}

export const api = {
  get: <T>(path: string, query?: RequestOptions["query"]) =>
    request<T>(path, { query }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: async <T>(path: string, file: File): Promise<T> => {
    const token = useAuthStore.getState().accessToken;
    const form = new FormData();
    form.append("file", file);
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    // no Content-Type: the browser sets the multipart boundary
    const res = await fetch(buildUrl(path), {
      method: "POST",
      headers,
      credentials: "include",
      body: form,
    });
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;
    if (!res.ok) {
      throw new ApiError(res.status, parseDetail(data) || res.statusText);
    }
    return data as T;
  },
  refresh: refreshAccessToken,
};
