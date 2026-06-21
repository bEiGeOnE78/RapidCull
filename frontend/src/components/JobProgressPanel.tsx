import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { useJobInvalidation } from '../hooks/useJobInvalidation'

interface Props {
  jobId: string | null
  label: string
  op: string
  activeGalleryId?: string | null
  onClose: () => void
}

const STATUS_COLOR: Record<string, string> = {
  running: '#f5a623',
  done: '#4caf50',
  failed: '#f44336',
}

export default function JobProgressPanel({ jobId, label, op, activeGalleryId, onClose }: Props) {
  const logRef = useRef<HTMLDivElement>(null)
  const invalidateForJobOp = useJobInvalidation()
  const prevStatusRef = useRef<string | undefined>(undefined)

  const { data } = useQuery({
    queryKey: ['job-progress', jobId],
    queryFn: () => api.getJobProgress(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'running' ? 1500 : false
    },
  })

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [data?.entries?.length])

  // Invalidate caches when job transitions to done
  useEffect(() => {
    const status = data?.status
    if (status === 'done' && prevStatusRef.current !== 'done' && op) {
      invalidateForJobOp(op, activeGalleryId ?? undefined)
    }
    prevStatusRef.current = status
  }, [data?.status, op, activeGalleryId, invalidateForJobOp])

  const status = data?.status ?? 'running'
  const entries = data?.entries ?? []

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        right: 0,
        width: 360,
        maxHeight: 300,
        background: '#1a1a1a',
        borderTop: '1px solid #333',
        borderLeft: '1px solid #333',
        boxShadow: '-4px -4px 24px rgba(0,0,0,0.5)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 200,
        fontFamily: 'inherit',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 12px',
          borderBottom: '1px solid #2a2a2a',
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 13, color: '#ccc', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {jobId ? label : 'No active job'}
        </span>
        {jobId && (
          <span
            style={{
              fontSize: 11,
              padding: '2px 6px',
              borderRadius: 10,
              background: STATUS_COLOR[status] ?? '#555',
              color: '#000',
              fontWeight: 600,
              flexShrink: 0,
            }}
          >
            {status}
          </span>
        )}
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#666',
            cursor: 'pointer',
            fontSize: 14,
            padding: '0 4px',
            lineHeight: 1,
            flexShrink: 0,
          }}
          title="Close"
        >
          ✕
        </button>
      </div>

      {/* Log area */}
      <div
        ref={logRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '8px 12px',
          minHeight: 0,
        }}
      >
        {!jobId && (
          <p style={{ color: '#555', fontSize: 12, margin: 0 }}>No active job.</p>
        )}
        {jobId && entries.length === 0 && (
          <p style={{ color: '#555', fontSize: 12, margin: 0 }}>Waiting for output...</p>
        )}
        {entries.map((entry, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              gap: 8,
              marginBottom: 4,
              fontFamily: 'monospace',
              fontSize: 11,
              lineHeight: 1.4,
            }}
          >
            <span style={{ color: '#555', flexShrink: 0 }}>
              {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
            <span style={{ color: '#bbb', wordBreak: 'break-word' }}>{entry.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
