import { useEffect, useState } from 'react'

import { SENSOR_BG, SENSOR_COLOR, SENSOR_LABEL, api, fmtTime } from '../api'
import Pager from '../components/Pager'
import { IconClock, IconSearch } from '../components/Icons'

// UC 5.2.3 - Xem lịch sử dữ liệu cảm biến. Lọc/sắp xếp/phân trang đều do backend xử lý.
export default function SensorData() {
  const [filters, setFilters] = useState({ q: '', time: '', type: '', sort: 'desc', limit: 8 })
  const [page, setPage] = useState(1)
  const [result, setResult] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const set = (key) => (e) => {
    setFilters((f) => ({ ...f, [key]: e.target.value }))
    setPage(1)
  }

  useEffect(() => {
    let alive = true
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await api.sensorData({ ...filters, page })
        if (alive) { setResult(data); setError('') }
      } catch (err) {
        if (alive) { setError(err.message); setResult({ items: [], total: 0 }) }
      } finally {
        if (alive) setLoading(false)
      }
    }, 250)   // gộp thao tác gõ liên tiếp thành một lần gọi API

    return () => { alive = false; clearTimeout(timer) }
  }, [filters, page])

  return (
    <>
      <div className="toolbar">
        <div className="search">
          <IconSearch />
          <input value={filters.q} onChange={set('q')} placeholder="Tìm theo tên cảm biến (DHT11, LDR)" />
        </div>
        <div className="search">
          <IconClock />
          <input value={filters.time} onChange={set('time')} placeholder="Tìm theo thời gian (yyyy/mm/dd-hh:mm:ss)" />
        </div>
        <div className="fl">
          <label htmlFor="sd-type">Loại</label>
          <select id="sd-type" value={filters.type} onChange={set('type')}>
            <option value="">Tất cả</option>
            <option value="temp">Nhiệt độ</option>
            <option value="humid">Độ ẩm</option>
            <option value="light">Ánh sáng</option>
          </select>
        </div>
        <div className="fl">
          <label htmlFor="sd-sort">Sắp xếp</label>
          <select id="sd-sort" value={filters.sort} onChange={set('sort')}>
            <option value="desc">Mới nhất</option>
            <option value="asc">Cũ nhất</option>
          </select>
        </div>
        <div className="fl">
          <label htmlFor="sd-limit">Số dòng</label>
          <select id="sd-limit" value={filters.limit} onChange={set('limit')}>
            <option>8</option><option>12</option><option>20</option>
          </select>
        </div>
      </div>

      <div className="tbl-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>TÊN CẢM BIẾN</th><th>LOẠI</th><th>GIÁ TRỊ</th><th>THỜI GIAN</th></tr>
          </thead>
          <tbody>
            {result.items.map((x) => (
              <tr key={x.id}>
                <td>{x.id}</td>
                <td style={{ fontWeight: 500 }}>{x.sensor_name}</td>
                <td>
                  <span className="badge" style={{ background: SENSOR_BG[x.type], color: SENSOR_COLOR[x.type] }}>
                    {SENSOR_LABEL[x.type]}
                  </span>
                </td>
                <td style={{ fontWeight: 500, color: SENSOR_COLOR[x.type] }}>
                  {x.value} {x.unit}
                </td>
                <td style={{ color: 'var(--text2)' }}>{fmtTime(x.recorded_at)}</td>
              </tr>
            ))}
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
