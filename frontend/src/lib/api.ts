const API_URL =
  (import.meta.env.VITE_API_URL as string) ||
  'http://127.0.0.1:8000'

type RequestInitEx = RequestInit & {
  auth?: boolean
}

async function request(
  path: string,
  init: RequestInitEx = {},
) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((init.headers as Record<string, string>) || {}),
  }

  if (init.auth) {
    const token = localStorage.getItem('cs_token')

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
  })

  const text = await res.text()

  let data: any = null

  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    const message =
      data?.detail ||
      data?.message ||
      'Request failed'

    throw new Error(message)
  }

  return data
}

export const api = {
  post: (
    path: string,
    body?: any,
    auth = false,
  ) =>
    request(path, {
      method: 'POST',
      body: JSON.stringify(body),
      auth,
    }),

  get: (
    path: string,
    auth = false,
  ) =>
    request(path, {
      method: 'GET',
      auth,
    }),

  patch: (
    path: string,
    body?: any,
    auth = false,
  ) =>
    request(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
      auth,
    }),
}