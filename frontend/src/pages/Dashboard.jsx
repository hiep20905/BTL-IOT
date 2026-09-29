import { useCallback, useEffect, useMemo, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  CategoryScale, Chart as ChartJS, Filler, Legend, LinearScale,
  LineElement, PointElement, Tooltip,
} from 'chart.js'

import { api } from '../api'
import { useDashboardSocket } from '../useDashboardSocket'
import { IconBulb, IconFan, IconGear, IconHumid, IconSun, IconTemp, IconWarn } from '../components/Icons'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

const MAX_POINTS = 15
const DEVICE_ICON = {
  1: <IconBulb style={{ fontSize: 24, color: 'var(--amber)' }} />,
  2: <IconFan style={{ fontSize: 24, color: 'var(--blue)' }} />,
}
const DEVICE_COLOR = { 1: '#EF9F27', 2: '#378ADD' }
const DEVICE_SUB = { 1: 'Bật/tắt đèn LED', 2: 'Bật/tắt quạt' }

const hms = (iso) => {
  const d = new Date(iso)
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

export default function Dashboard() {
  const [points, setPoints] = useState([])       // [{temp, humid, light, at}] cũ -> mới
  const [devices, setDevices] = useState([])
  const [pending, setPending] = useState({})     // { [device_id]: true } khi đang chờ phản hồi
  const [offline, setOffline] = useState(false)
  const [alert, setAlert] = useState('')

  // --- Khởi tạo: gọi api/sensor-data/latest + api/devices/status (UC 5.2.2 bước 2) ---
  useEffect(() => {
    let alive = true

    const init = async () => {
      try {
        const [latest, devs, history] = await Promise.all([
          api.latestSensor(),
          api.deviceStatus(),
          api.sensorData({ limit: MAX_POINTS * 3, sort: 'desc' }),
        ])
        if (!alive) return

        setDevices(devs)

        // Gom bản ghi lịch sử theo mốc thời gian để dựng biểu đồ ban đầu
        const byTime = new Map()
        for (const it of history.items) {
          const group = byTime.get(it.recorded_at) ?? { at: it.recorded_at }
          group[it.type] = it.value
          byTime.set(it.recorded_at, group)
        }
        const seeded = [...byTime.values()]
          .sort((a, b) => new Date(a.at) - new Date(b.at))
          .slice(-MAX_POINTS)

        if (seeded.length) {
          setPoints(seeded)
        } else if (latest.recorded_at) {
          setPoints([{ ...latest, at: latest.recorded_at }])
        }
      } catch (err) {
        if (alive) setAlert(err.message)
      }
    }

    init()
    return () => { alive = false }
  }, [])

  // --- Kênh realtime ---
  const onSensorData = useCallback((data) => {
    setPoints((prev) => [...prev, data].slice(-MAX_POINTS))
  }, [])

  const onDeviceStatus = useCallback((data) => {
    setPending((prev) => {
      const next = { ...prev }
      delete next[data.device_id]
      return next
    })

    if (data.result === 'timeout') {
      setAlert(`Thiết bị #${data.device_id} không phản hồi. Lệnh đã được ghi nhận là TIMEOUT.`)
      return
    }

    setAlert('')
    setDevices((prev) =>
      prev.map((d) => (d.device_id === data.device_id ? { ...d, status: data.status } : d)),
    )
  }, [])

  const onDeviceOffline = useCallback((data) => {
    setOffline(data.offline)
    if (!data.offline) setAlert('')
  }, [])

  const wsConnected = useDashboardSocket({
    sensor_data: onSensorData,
    device_status: onDeviceStatus,
    device_offline: onDeviceOffline,
  })

  // --- Điều khiển thiết bị (UC 5.2.1) ---
  const toggle = async (device) => {
    const action = device.status === 'on' ? 'off' : 'on'
    setPending((prev) => ({ ...prev, [device.device_id]: true }))
    setAlert('')
    try {
      await api.sendAction(device.device_id, action)
      // Không lật công tắc ngay: chờ sự kiện device_status phản ánh trạng thái vật lý thật.
    } catch (err) {
      setPending((prev) => {
        const next = { ...prev }
        delete next[device.device_id]
        return next
      })
      setAlert(err.message)
    }
  }

  const current = points.at(-1) ?? {}

  const chartData = useMemo(() => ({
    labels: points.map((p) => hms(p.at)),
    datasets: [
      { label: 'Nhiệt độ (°C)', data: points.map((p) => p.temp), yAxisID: 'yL', borderColor: '#E24B4A', tension: 0.4, borderWidth: 2.5, pointRadius: 0 },
      { label: 'Độ ẩm (%)', data: points.map((p) => p.humid), yAxisID: 'yL', borderColor: '#378ADD', tension: 0.4, borderWidth: 2.5, pointRadius: 0 },
      { label: 'Ánh sáng (Lux)', data: points.map((p) => p.light), yAxisID: 'yR', borderColor: '#EF9F27', tension: 0.4, borderWidth: 2.5, pointRadius: 0 },
    ],
  }), [points])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (c) => {
            const unit = c.dataset.label.includes('Nhiệt') ? '°C'
              : c.dataset.label.includes('ẩm') ? '%' : ' Lux'
            return `${c.dataset.label.replace(/\s*\(.*\)/, '')}: ${Math.round(c.parsed.y)}${unit}`
          },
        },
      },
    },
    scales: {
      x: { grid: { color: '#2a2a2a' }, ticks: { color: '#a0a0a0', maxRotation: 0, autoSkip: true, maxTicksLimit: 6 } },
      yL: { type: 'linear', position: 'left', min: 0, max: 100, grid: { color: '#2a2a2a' }, ticks: { color: '#a0a0a0' }, title: { display: true, text: '°C / %', color: '#a0a0a0' } },
      yR: { type: 'linear', position: 'right', min: 0, max: 4095, grid: { drawOnChartArea: false }, ticks: { color: '#a0a0a0' }, title: { display: true, text: 'Lux', color: '#a0a0a0' } },
    },
  }), [])

  const fmtVal = (v, suffix) => (v === undefined || v === null ? '—' : `${v}${suffix}`)

  return (
    <>
      {offline && (
        <div className="banner">
          <IconWarn style={{ fontSize: 18 }} />
          Mất kết nối với thiết bị cảm biến — số liệu đang hiển thị là giá trị ghi nhận gần nhất.
        </div>
      )}
      {alert && (
        <div className="banner">
          <IconWarn style={{ fontSize: 18 }} />
          {alert}
        </div>
      )}

      <div className="layout">
        <div className="left">
          <div className="stats">
            <div className="card stat">
              <div className="icon" style={{ background: 'var(--bg-red)', color: 'var(--red)' }}><IconTemp /></div>
              <div><div className="lbl">Nhiệt độ</div><div className="val">{fmtVal(current.temp, '°C')}</div></div>
            </div>
            <div className="card stat">
              <div className="icon" style={{ background: 'var(--bg-blue)', color: 'var(--blue)' }}><IconHumid /></div>
              <div><div className="lbl">Độ ẩm</div><div className="val">{fmtVal(current.humid, '%')}</div></div>
            </div>
            <div className="card stat">
              <div className="icon" style={{ background: 'var(--bg-amber)', color: 'var(--amber)' }}><IconSun /></div>
              <div><div className="lbl">Ánh sáng</div><div className="val">{fmtVal(current.light, ' Lux')}</div></div>
            </div>
          </div>

          <div className="card">
            <div className="chart-head">
              <span className="chart-title">Biểu đồ thời gian thực</span>
              <div className="legend">
                <span className="lg"><i style={{ background: 'var(--red)' }} />Nhiệt độ (°C)</span>
                <span className="lg"><i style={{ background: 'var(--blue)' }} />Độ ẩm (%)</span>
                <span className="lg"><i style={{ background: 'var(--amber)' }} />Ánh sáng (Lux)</span>
              </div>
              <span className={`conn ${wsConnected ? 'ok' : 'off'}`} style={{ marginLeft: 'auto' }}>
                <i />{wsConnected ? 'Realtime' : 'Mất kết nối'}
              </span>
            </div>
            <div style={{ position: 'relative', height: 320 }}>
              <Line data={chartData} options={chartOptions} />
            </div>
          </div>
        </div>

        <div className="card" style={{ alignSelf: 'start' }}>
          <div className="panel-title"><IconGear style={{ fontSize: 22 }} />Bảng điều khiển</div>

          {devices.map((d) => {
            const on = d.status === 'on'
            const busy = !!pending[d.device_id]
            const color = DEVICE_COLOR[d.device_id] ?? '#5DCAA5'
            return (
              <div className="dev" key={d.device_id}>
                <div className="dev-row">
                  <div className="dev-info">
                    {DEVICE_ICON[d.device_id]}
                    <div>
                      <div className="dev-name">{d.device_name}</div>
                      <div className="dev-sub">{DEVICE_SUB[d.device_id] ?? 'Bật/tắt thiết bị'}</div>
                    </div>
                  </div>
                  <button
                    className="toggle"
                    disabled={busy}
                    onClick={() => toggle(d)}
                    aria-label={`Bật/tắt ${d.device_name}`}
                    style={{ background: on ? color : '#3a3a3a' }}
                  >
                    <span className="knob" style={{ left: on ? 27 : 3 }} />
                  </button>
                </div>
                <div className="status" style={{ color: busy ? 'var(--amber)' : on ? color : 'var(--text2)' }}>
                  {busy ? 'Đang chờ phản hồi từ thiết bị…' : `Trạng thái: ${on ? 'BẬT' : 'TẮT'}`}
                </div>
              </div>
            )
          })}

          {devices.length === 0 && <div className="empty">Chưa có thiết bị nào</div>}
        </div>
      </div>
    </>
  )
}
