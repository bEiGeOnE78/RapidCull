import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

interface TrashPanelProps {
  isOpen: boolean
  onClose: () => void
}

function shortPath(fullPath: string): string {
  const parts = fullPath.replace(/\\/g, '/').split('/')
  if (parts.length <= 2) return fullPath
  return `…/${parts[parts.length - 2]}/${parts[parts.length - 1]}`
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export default function TrashPanel({ isOpen, onClose }: TrashPanelProps) {
  const queryClient = useQueryClient()

  const trashQuery = useQuery({
    queryKey: ['trash'],
    queryFn: () => api.getTrash(),
    enabled: isOpen,
  })

  const restoreMutation = useMutation({
    mutationFn: (imageId: string) => api.restoreTrash(imageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trash'] })
    },
  })

  if (!isOpen) return null

  const items = trashQuery.data?.items ?? []
  const count = trashQuery.data?.count ?? 0

  const btnStyle: React.CSSProperties = {
    background: 'transparent',
    border: '1px solid #555',
    color: '#aaa',
    borderRadius: 4,
    padding: '2px 8px',
    cursor: 'pointer',
    fontSize: 11,
    flexShrink: 0,
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 80,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        style={{
          width: 600,
          height: 500,
          background: '#222',
          border: '1px solid #444',
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderBottom: '1px solid #333',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 16, fontWeight: 600, color: '#e0e0e0' }}>Trash</span>
            {!trashQuery.isLoading && (
              <span
                style={{
                  fontSize: 11,
                  color: '#888',
                  background: '#333',
                  borderRadius: 10,
                  padding: '1px 8px',
                }}
              >
                {count}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#aaa',
              cursor: 'pointer',
              fontSize: 16,
              lineHeight: 1,
              padding: '2px 6px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
          {trashQuery.isLoading && (
            <div style={{ color: '#888', fontSize: 13 }}>Loading...</div>
          )}
          {!trashQuery.isLoading && items.length === 0 && (
            <div style={{ color: '#666', fontSize: 13 }}>Trash is empty.</div>
          )}
          {items.map((item) => (
            <div
              key={item.image_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 0',
                borderBottom: '1px solid #2a2a2a',
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    color: '#d0d0d0',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                  title={item.original_path}
                >
                  {shortPath(item.original_path)}
                </div>
                <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>
                  {formatDate(item.trashed_at)}
                </div>
              </div>
              <button
                style={btnStyle}
                onClick={() => restoreMutation.mutate(item.image_id)}
                disabled={restoreMutation.isPending}
              >
                Restore
              </button>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div
          style={{
            padding: '8px 16px',
            borderTop: '1px solid #2a2a2a',
            fontSize: 11,
            color: '#555',
            flexShrink: 0,
          }}
        >
          Hard delete trash permanently via Command Palette (/).
        </div>
      </div>
    </div>
  )
}
