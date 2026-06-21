import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

interface FaceAssignPopoverProps {
  faceId: string
  currentPersonId: string | null
  imageId: string
  anchorRect: DOMRect
  onClose: () => void
}

export default function FaceAssignPopover({
  faceId,
  currentPersonId,
  imageId,
  anchorRect,
  onClose,
}: FaceAssignPopoverProps) {
  const [search, setSearch] = useState('')
  const popoverRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const personsQuery = useQuery({
    queryKey: ['persons'],
    queryFn: () => api.getPersons(),
  })

  const assignMutation = useMutation({
    mutationFn: (personId: string | null) => api.assignFace(faceId, personId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image', imageId, 'faces'] })
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      onClose()
    },
  })

  // ESC to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Click outside to close
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    // Delay so the click that opened us doesn't immediately close
    const id = setTimeout(() => window.addEventListener('mousedown', handler), 50)
    return () => {
      clearTimeout(id)
      window.removeEventListener('mousedown', handler)
    }
  }, [onClose])

  const persons = personsQuery.data?.persons ?? []
  const filtered = search.trim()
    ? persons.filter((p) => p.name.toLowerCase().includes(search.trim().toLowerCase()))
    : persons

  // Position: below and to the right of the anchor box, clamped to viewport
  const POPOVER_W = 240
  const POPOVER_H = 300
  let left = anchorRect.right + 8
  let top = anchorRect.top
  if (left + POPOVER_W > window.innerWidth - 8) {
    left = anchorRect.left - POPOVER_W - 8
  }
  if (top + POPOVER_H > window.innerHeight - 8) {
    top = window.innerHeight - POPOVER_H - 8
  }
  if (top < 8) top = 8
  if (left < 8) left = 8

  return (
    <div
      ref={popoverRef}
      style={{
        position: 'fixed',
        left,
        top,
        width: POPOVER_W,
        maxHeight: POPOVER_H,
        background: '#1e1e1e',
        border: '1px solid #444',
        borderRadius: 6,
        boxShadow: '0 4px 24px rgba(0,0,0,0.6)',
        zIndex: 200,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        pointerEvents: 'auto',
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Search */}
      <div style={{ padding: '8px 10px', borderBottom: '1px solid #333', flexShrink: 0 }}>
        <input
          autoFocus
          placeholder="Search person…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%',
            background: '#2a2a2a',
            border: '1px solid #555',
            borderRadius: 4,
            color: '#e0e0e0',
            fontSize: 12,
            padding: '4px 8px',
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Person list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {personsQuery.isLoading && (
          <div style={{ color: '#888', fontSize: 12, padding: '8px 10px' }}>Loading…</div>
        )}
        {filtered.map((person) => {
          const isCurrent = person.person_id === currentPersonId
          return (
            <button
              key={person.person_id}
              disabled={assignMutation.isPending}
              onClick={() => assignMutation.mutate(person.person_id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                width: '100%',
                background: isCurrent ? '#2a3a2a' : 'transparent',
                border: 'none',
                borderBottom: '1px solid #2a2a2a',
                color: '#d0d0d0',
                cursor: 'pointer',
                padding: '6px 10px',
                textAlign: 'left',
              }}
            >
              <img
                src={api.getPersonThumbnailUrl(person.person_id, person.face_count)}
                width={32}
                height={32}
                style={{ borderRadius: 4, objectFit: 'cover', flexShrink: 0 }}
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }}
                alt=""
              />
              <span style={{ flex: 1, fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {person.name}
              </span>
              <span style={{ fontSize: 11, color: '#666', flexShrink: 0 }}>
                {person.face_count}
              </span>
            </button>
          )
        })}
        {!personsQuery.isLoading && filtered.length === 0 && (
          <div style={{ color: '#666', fontSize: 12, padding: '8px 10px' }}>No matches</div>
        )}
      </div>

      {/* Unassign footer */}
      <div style={{ padding: '6px 10px', borderTop: '1px solid #333', flexShrink: 0 }}>
        <button
          disabled={assignMutation.isPending || currentPersonId === null}
          onClick={() => assignMutation.mutate(null)}
          style={{
            width: '100%',
            background: 'transparent',
            border: '1px solid #744',
            borderRadius: 4,
            color: currentPersonId ? '#f88' : '#555',
            cursor: currentPersonId ? 'pointer' : 'default',
            fontSize: 11,
            padding: '4px 0',
          }}
        >
          Unassign
        </button>
      </div>
    </div>
  )
}
