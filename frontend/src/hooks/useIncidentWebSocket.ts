import { useEffect, useRef } from 'react'
import { toast } from 'sonner'

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useIncidentWebSocket(
  incidentId: string | undefined,
  onEvent: () => void,
) {
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    if (!incidentId) return

    let cancelled = false
    let ws: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout>

    function connect() {
      if (cancelled) return
      ws = new WebSocket(`${WS_BASE}/ws/incidents/${incidentId}`)

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data)
          if (data.type === 'error' && data.payload?.message) {
            toast.error(data.payload.message, {
              description: `Stage: ${data.payload.stage ?? 'unknown'}`,
            })
          }
        } catch {
          // non-JSON message — ignore
        }
        onEventRef.current()
      }

      ws.onclose = () => {
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, 2000)
        }
      }
    }

    connect()

    return () => {
      cancelled = true
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [incidentId])
}
