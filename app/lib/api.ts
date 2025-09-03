const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";

export function authHeaders(token?: string) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function api(path: string, opts: RequestInit = {}, token?: string) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(opts.headers||{}), ...authHeaders(token) },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
