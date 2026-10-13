let csrf = '';
export function setCsrf(token: string) {
  csrf = token;
}
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api' + path, {
    method,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(method !== 'GET' ? { 'X-CSRF-Token': csrf } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: 'Server unavailable' }));
    throw new Error(
      typeof data.detail === 'string'
        ? data.detail
        : data.detail?.map((e: { msg: string }) => e.msg).join('; ') || 'Request failed',
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
