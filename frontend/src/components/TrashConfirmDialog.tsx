import type { Gallery } from '../api/client'

interface Props {
  isOpen: boolean
  affectedImages: Array<{ image_id: string; galleries: Gallery[] }>
  onConfirm: () => void
  onCancel: () => void
}

export default function TrashConfirmDialog({ isOpen, affectedImages, onConfirm, onCancel }: Props) {
  if (!isOpen) return null

  return (
    <div
      onClick={onCancel}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(10px)',
        zIndex: 300,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#222',
          border: '1px solid #444',
          borderRadius: 8,
          padding: '24px',
          width: 440,
          maxHeight: '70vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 24px 64px rgba(0,0,0,0.8)',
        }}
      >
        <div style={{ fontSize: 14, color: '#f88', fontWeight: 600, marginBottom: 8 }}>
          Warning: images belong to multiple galleries
        </div>
        <div style={{ fontSize: 12, color: '#aaa', marginBottom: 16 }}>
          The following images will be permanently trashed and removed from all galleries:
        </div>
        <div style={{ overflowY: 'auto', flex: 1, marginBottom: 16 }}>
          {affectedImages.map(({ image_id, galleries }) => (
            <div
              key={image_id}
              style={{
                marginBottom: 10,
                padding: '8px 10px',
                background: '#1a1a1a',
                borderRadius: 4,
                border: '1px solid #333',
              }}
            >
              <div style={{ fontSize: 11, color: '#888', marginBottom: 4, fontFamily: 'monospace' }}>
                {image_id}
              </div>
              <div style={{ fontSize: 11, color: '#aaa' }}>
                In galleries:{' '}
                {galleries.map((g, i) => (
                  <span key={g.gallery_id}>
                    <span style={{ color: '#ccc' }}>{g.name}</span>
                    {i < galleries.length - 1 ? ', ' : ''}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', flexShrink: 0 }}>
          <button
            onClick={onCancel}
            style={{
              background: 'transparent',
              border: '1px solid #444',
              color: '#aaa',
              borderRadius: 4,
              padding: '6px 14px',
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            style={{
              background: '#c0392b',
              border: 'none',
              color: '#fff',
              borderRadius: 4,
              padding: '6px 14px',
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            Trash anyway
          </button>
        </div>
      </div>
    </div>
  )
}
