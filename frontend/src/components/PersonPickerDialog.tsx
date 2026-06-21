import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Person } from '../api/client'

interface Props {
  onPick: (person: Person) => void
  onCancel: () => void
}

export default function PersonPickerDialog({ onPick, onCancel }: Props) {
  const [search, setSearch] = useState('')

  const personsQuery = useQuery({
    queryKey: ['persons'],
    queryFn: () => api.getPersons(),
  })

  // ESC to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onCancel])

  const persons = personsQuery.data?.persons ?? []
  const filtered = search.trim()
    ? persons.filter((p) => p.name.toLowerCase().includes(search.trim().toLowerCase()))
    : persons

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
          <div style={{ fontSize: 13, color: '#aaa', marginBottom: 8 }}>Choose a person</div>
          <input
            autoFocus
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search..."
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

        {/* Person list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {personsQuery.isLoading && (
            <div style={{ color: '#888', fontSize: 13, padding: '12px 16px' }}>Loading...</div>
          )}
          {!personsQuery.isLoading && filtered.length === 0 && (
            <div style={{ color: '#666', fontSize: 13, padding: '12px 16px' }}>No persons found</div>
          )}
          {filtered.map((person) => (
            <button
              key={person.person_id}
              onClick={() => onPick(person)}
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
                padding: '8px 16px',
                textAlign: 'left',
              }}
            >
              <img
                src={api.getPersonThumbnailUrl(person.person_id, person.face_count)}
                width={40}
                height={40}
                style={{ borderRadius: 4, objectFit: 'cover', flexShrink: 0 }}
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }}
                alt=""
              />
              <span style={{ flex: 1, fontSize: 13 }}>{person.name}</span>
              <span style={{ fontSize: 11, color: '#888' }}>
                {person.face_count} face{person.face_count !== 1 ? 's' : ''}
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
