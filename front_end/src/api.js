// Mọi lời gọi backend đi qua đây. Dev: proxy /api -> :8000 (vite.config.js). Build: đặt VITE_API_URL.
const BASE = import.meta.env.VITE_API_URL ?? '/api'

async function request(path, options) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, options)
  } catch {
    throw new Error('Không kết nối được tới máy chủ. Kiểm tra backend đã chạy ở cổng 8000 chưa.')
  }
  if (!res.ok) {
    let detail = `Lỗi ${res.status}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* giữ thông báo mặc định */
    }
    throw new Error(detail)
  }
  return res.json()
}

function toQuery(params) {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') qs.set(k, v)
  }
  return qs.toString()
}

export const getHealth = (signal) => request('/health', { signal })

export const listJobs = (params, signal) => request(`/jobs?${toQuery(params)}`, { signal })

export const searchJobs = (params, signal) => request(`/jobs/search?${toQuery(params)}`, { signal })

export const getJob = (id, signal) => request(`/jobs/${encodeURIComponent(id)}`, { signal })

export function parseCv(file, signal) {
  const body = new FormData()
  body.append('file', file)
  return request('/cv/parse', { method: 'POST', body, signal })
}
