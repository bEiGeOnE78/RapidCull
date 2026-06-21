import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Gallery } from '../api/client'

interface Props {
  count: number
  onPick: (gallery: Gallery) => void
  onCancel: () => void
}

export default function AddToExistingGalleryDialog({ count, onPick, onCancel }: Props) {
  const [search, setSearch] = useState('')

  const galleriesQuery = useQuery({
    queryKey: ['galleries'],
    queryFn: () => api.getGalleries(),
  })

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onCancel])

  const galleries = (galleriesQuery.data?.galleries ?? []).filter((g) => g.type === 'user')
  const filtered = search.trim()
    ? galleries.filter((g) => g.name.toLowerCase().includes(search.trim().toLowerCase()))
    : galleries

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
          width: 400,
          maxHeight: 500,
          boxShadow: '0 24px 64px rgba(0,0,0,0.8)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #333', background: '#111' }}>
          <div style={{ fontSize: 13, color: '#aaa', marginBottom: 8 }}>
            Add {count} image{count !== 1 ? 's' : ''} to gallery
          </div>
          <input
            autoFocus
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search galleries..."
            style={{
              width: '100%',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#e0e0e0',
              fontSize: 14,
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Gallery list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {galleriesQuery.isLoading && (
            <div style={{ color: '#888', fontSize: 13, padding: '12px 16px' }}>Loading...</div>
          )}
          {!galleriesQuery.isLoading && filtered.length === 0 && (
            <div style={{ color: '#666', fontSize: 13, padding: '12px 16px' }}>
              No user galleries found
            </div>
          )}
          {filtered.map((gallery) => (
            <button
              key={gallery.gallery_id}
              onClick={() => onPick(gallery)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                width: '100%',
                background: 'transparent',
                border: 'none',
                borderBottom: '1px solid #2a2a2a',
                color: '#d0d0d0',
                cursor: 'pointer',
                padding: '10px 16px',
                textAlign: 'left',
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = '#2a2a2a' }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
            >
              <span style={{ flex: 1, fontSize: 13 }}>{gallery.name}</span>
              <span
                style={{
                  fontSize: 11,
                  background: '#333',
                  color: '#aaa',
                  borderRadius: 10,
                  padding: '1px 7px',
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                }}
              >
                {gallery.count}
              </span>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div style={{ padding: '8px 16px', borderTop: '1px solid #333' }}>
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
        </div>
      </div>
    </div>
  )
}
