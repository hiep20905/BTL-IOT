import { useEffect, useState } from 'react'

import { clearToken, getToken } from './api'
import ActionHistory from './pages/ActionHistory'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Profile from './pages/Profile'
import SensorData from './pages/SensorData'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', Page: Dashboard },
  { id: 'sensor', label: 'Sensor Data', Page: SensorData },
  { id: 'action', label: 'Action History', Page: ActionHistory },
  { id: 'profile', label: 'Profile', Page: Profile },
]

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken())
  const [tab, setTab] = useState('dashboard')

  // api.js phát sự kiện này khi gặp HTTP 401 (token sai/hết hạn).
  useEffect(() => {
    const onUnauthorized = () => setAuthed(false)
    window.addEventListener('iot:unauthorized', onUnauthorized)
    return () => window.removeEventListener('iot:unauthorized', onUnauthorized)
  }, [])

  if (!authed) {
    return <Login onSuccess={() => { setTab('dashboard'); setAuthed(true) }} />
  }

  const logout = () => {
    clearToken()
    setAuthed(false)
  }

  const { Page } = TABS.find((t) => t.id === tab)

  return (
    <>
      <nav className="nav">
        {TABS.map((t) => (
          <button key={t.id} className={t.id === tab ? 'active' : ''} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
        <div className="right">
          <button className="logout" onClick={logout}>Đăng xuất</button>
        </div>
      </nav>

      {/* key ép remount khi đổi tab để mỗi trang tự nạp lại dữ liệu */}
      <Page key={tab} />
    </>
  )
}
