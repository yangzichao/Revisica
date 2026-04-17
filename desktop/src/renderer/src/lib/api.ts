export function apiFetch(
  apiBase: string,
  apiToken: string,
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const headers = new Headers(init.headers)
  if (apiToken) {
    headers.set('Authorization', `Bearer ${apiToken}`)
  }
  return fetch(`${apiBase}${path}`, { ...init, headers })
}
