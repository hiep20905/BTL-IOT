import { useEffect, useRef, useState } from 'react'
import { getToken } from './api'

/**
 * Kết nối WebSocket /ws/dashboard (mục 4.3.4 SRS) và gọi lại handler theo tên sự kiện.
 * Tự kết nối lại sau 3 giây nếu đứt kết nối.
 *
 * @param {{sensor_data?:Function, device_status?:Function, device_offline?:Function}} handlers
 * @returns {boolean} trạng thái kết nối hiện tại
 */
export function useDashboardSocket(handlers) {
  const [connected, setConnected] = useState(false)
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  useEffect(() => {
    const token = getToken()
    if (!token) return

    let ws
    let retryTimer
    let closed = false

    const connect = () => {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${window.location.host}/ws/dashboard?token=${token}`)

      ws.onopen = () => setConnected(true)

      ws.onmessage = (e) => {
        try {
          const { event, data } = JSON.parse(e.data)
          handlersRef.current[event]?.(data)
        } catch {
          /* bỏ qua bản tin không đúng định dạng */
        }
      }

      ws.onclose = () => {
        setConnected(false)
        if (!closed) retryTimer = setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      closed = true
      clearTimeout(retryTimer)
      ws?.close()
    }
  }, [])

  return connected
}
