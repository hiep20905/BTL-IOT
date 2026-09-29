import { useState } from 'react'
import { api, setToken } from '../api'

export default function Login({ onSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const data = await api.login(username, password)
      setToken(data.token)
      onSuccess()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-wrap">
      <form className="card login-card" onSubmit={submit}>
        <h1>Đăng nhập</h1>
        <p className="sub">Hệ thống giám sát &amp; điều khiển IoT qua MQTT</p>

        {error && <div className="err">{error}</div>}

        <div className="field">
          <label htmlFor="u">Tên đăng nhập</label>
          <input id="u" value={username} onChange={(e) => setUsername(e.target.value)}
                 autoComplete="username" required />
        </div>
        <div className="field">
          <label htmlFor="p">Mật khẩu</label>
          <input id="p" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 autoComplete="current-password" required />
        </div>

        <button className="btn" type="submit" disabled={busy}>
          {busy ? 'Đang đăng nhập…' : 'Đăng nhập'}
        </button>
        <p className="hint">Tài khoản mặc định: hiep / 123456</p>
      </form>
    </div>
  )
}
