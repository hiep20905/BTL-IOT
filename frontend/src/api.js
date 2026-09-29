// Lớp gọi RESTful API theo quy ước mục 4.3.1 SRS:
// mọi phản hồi có dạng { success, data, message }; xác thực bằng "Authorization: Bearer <token>".

const TOKEN_KEY = 'iot_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(`/api${path}`, window.location.origin)
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    }
  }

  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new ApiError(0, 'Không kết nối được tới máy chủ')
  }

  const payload = await res.json().catch(() => ({}))

  if (res.status === 401) {
    clearToken()
    window.dispatchEvent(new Event('iot:unauthorized'))
  }
  if (!res.ok) throw new ApiError(res.status, payload.message || `Lỗi ${res.status}`)

  return payload.data
}

export const api = {
  login: (username, password) =>
    request('/auth/login', { method: 'POST', body: { username, password } }),
  me: () => request('/users/me'),
  latestSensor: () => request('/sensor-data/latest'),
  sensorData: (params) => request('/sensor-data', { params }),
  deviceStatus: () => request('/devices/status'),
  actions: (params) => request('/actions', { params }),
  sendAction: (deviceId, action) =>
    request(`/actions/${deviceId}`, { method: 'POST', body: { action } }),
}

// --- tiện ích hiển thị dùng chung ---

// yyyy/mm/dd-hh:mm:ss, giống định dạng trong bản thiết kế giao diện
export function fmtTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}/${p(d.getMonth() + 1)}/${p(d.getDate())}-${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

export const SENSOR_LABEL = { temp: 'Nhiệt độ', humid: 'Độ ẩm', light: 'Ánh sáng' }
export const SENSOR_COLOR = { temp: 'var(--red)', humid: 'var(--blue)', light: 'var(--amber)' }
export const SENSOR_BG = { temp: 'var(--bg-red)', humid: 'var(--bg-blue)', light: 'var(--bg-amber)' }

export const STATUS_INFO = {
  SUCCESS: { text: 'Thành công', color: 'var(--green)', bg: 'var(--bg-green)' },
  PENDING: { text: 'Đang chờ…', color: 'var(--amber)', bg: 'var(--bg-amber)' },
  TIMEOUT: { text: 'Quá hạn', color: 'var(--red)', bg: 'var(--bg-red)' },
}
