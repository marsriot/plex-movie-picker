// Thin wrapper around the backend API. In dev, Vite proxies /api to :8787.

async function get(path, params) {
  const qs = params ? '?' + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v != null))
  ) : ''
  const res = await fetch(`/api${path}${qs}`)
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: body ? { 'content-type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText)
  return res.json()
}

export const api = {
  status: () => get('/status'),
  sync: () => post('/sync'),
  movies: (params) => get('/movies', params),
  genres: () => get('/genres'),
  gems: (params) => get('/gems', params),
  random: (params) => get('/random', params),
  bracket: (params) => get('/bracket', params),
  mood: (body) => post('/mood', body),
}

// Poster URL for a Plex thumb path (proxied through the backend).
export const posterUrl = (thumb) =>
  thumb ? `/api/poster?path=${encodeURIComponent(thumb)}` : null
