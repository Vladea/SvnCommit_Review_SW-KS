const BASE = process.env.NEXT_PUBLIC_API_BASE || '';

interface RequestOptions extends RequestInit {
  timeout?: number;
}

async function request<T>(url: string, options?: RequestOptions): Promise<T> {
  const { timeout = 30000, ...fetchOptions } = options || {};
  const controller = new AbortController();
  const timer = timeout > 0 ? setTimeout(() => controller.abort(), timeout) : null;
  try {
    const res = await fetch(BASE + url, {
      signal: controller.signal,
      ...fetchOptions,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export const api = {
  get: <T>(url: string, options?: RequestOptions) => request<T>(url, options),
  post: <T>(url: string, body?: unknown, options?: RequestOptions) =>
    request<T>(url, {
      method: 'POST',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  put: <T>(url: string, body?: unknown, options?: RequestOptions) =>
    request<T>(url, {
      method: 'PUT',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  del: <T>(url: string, options?: RequestOptions) => request<T>(url, { method: 'DELETE', ...options }),
};
