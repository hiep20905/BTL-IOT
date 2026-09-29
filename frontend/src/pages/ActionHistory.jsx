import { useEffect, useState } from 'react'

import { STATUS_INFO, api, fmtTime } from '../api'
import Pager from '../components/Pager'
import { IconClock, IconSearch } from '../components/Icons'

// UC 5.2.4 - Xem lịch sử điều khiển thiết bị.
export default function ActionHistory() {
  const [devices, setDevices] = useState([])
  const [filters, setFilters] = useState({
    q: '', time: '', device_id: '', action: '', status: '', sort: 'desc', limit: 8,
  })
  const [page, setPage] = useState(1)
  const [result, setResult] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const set = (key) => (e) => {
    setFilters((f) => ({ ...f, [key]: e.target.value }))
    setPage(1)
  }

  useEffect(() => {
    api.deviceStatus().then(setDevices).catch(() => setDevices([]))
  }, [])

  useEffect(() => {
    let alive = true
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await api.actions({ ...filters, page })
        if (alive) { setResult(data); setError('') }
      } catch (err) {
        if (alive) { setError(err.message); setResult({ items: [], total: 0 }) }
      } finally {
        if (alive) setLoading(false)
      }
    }, 250)

    return () => { alive = false; clearTimeout(timer) }
  }, [filters, page])

  return (
    <>
      <div className="toolbar">
        <div className="search">
          <IconSearch />
          <input value={filters.q} onChange={set('q')} placeholder="Tìm theo tên thiết bị" />
        </div>
        <div className="search">
          <IconClock />
          <input value={filters.time} onChange={set('time')} placeholder="Tìm theo thời gian (yyyy/mm/dd-hh:mm:ss)" />
        </div>
        <div className="fl">
          <label htmlFor="ah-dev">Thiết bị</label>
          <select id="ah-dev" value={filters.device_id} onChange={set('device_id')}>
            <option value="">Tất cả</option>
            {devices.map((d) => (
              <option key={d.device_id} value={d.device_id}>{d.device_name}</option>
            ))}
          </select>
        </div>
        <div className="fl">
          <label htmlFor="ah-act">Hành động</label>
          <select id="ah-act" value={filters.action} onChange={set('action')}>
            <option value="">Tất cả</option>
            <option value="ON">Bật</option>
            <option value="OFF">Tắt</option>
          </select>
        </div>
        <div className="fl">
          <label htmlFor="ah-st">Trạng thái</label>
          <select id="ah-st" value={filters.status} onChange={set('status')}>
            <option value="">Tất cả</option>
            <option value="SUCCESS">Thành công</option>
            <option value="PENDING">Đang chờ</option>
            <option value="TIMEOUT">Quá hạn</option>
          </select>
        </div>
        <div className="fl">
          <label htmlFor="ah-limit">Số dòng</label>
          <select id="ah-limit" value={filters.limit} onChange={set('limit')}>
            <option>8</option><option>12</option><option>20</option>
          </select>
        </div>
      </div>

      <div className="tbl-wrap">
        <table>
          <thead>
            <tr><th>MÃ LỆNH</th><th>MÃ TB</th><th>THIẾT BỊ</th><th>HÀNH ĐỘNG</th><th>TRẠNG THÁI</th><th>THỜI GIAN</th></tr>
          </thead>
          <tbody>
            {result.items.map((x) => {
              const st = STATUS_INFO[x.status] ?? { text: x.status, color: 'var(--text2)', bg: 'var(--surface2)' }
              const isOn = x.action === 'on'
              return (
                <tr key={x.action_id}>
                  <td>{x.action_id}</td>
                  <td>{x.device_id}</td>
                  <td style={{ fontWeight: 500 }}>{x.device_name}</td>
                  <td>
                    <span className="badge" style={{
                      background: isOn ? 'var(--bg-blue)' : 'var(--bg-red)',
                      color: isOn ? 'var(--blue)' : 'var(--red)',
                    }}>
                      {x.action.toUpperCase()}
                    </span>
                  </td>
                  <td><span className="badge" style={{ background: st.bg, color: st.color }}>{st.text}</span></td>
                  <td style={{ color: 'var(--text2)' }}>{fmtTime(x.created_at)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {!loading && result.items.length === 0 && (
          <div className="empty">{error || 'Không tìm thấy dữ liệu'}</div>
        )}
        {loading && result.items.length === 0 && <div className="empty">Đang tải…</div>}
      </div>

      <Pager page={page} limit={Number(filters.limit)} total={result.total} onPage={setPage} />
    </>
  )
}
