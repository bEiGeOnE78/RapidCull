import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Person } from '../api/client'

interface MergePersonPickerProps {
  sourcePersonId: string
  sourcePersonName: string
  anchorRect: DOMRect
  onClose: () => void
}

export default function MergePersonPicker({
  sourcePersonId,
  sourcePersonName,
  anchorRect,
  onClose,
}: MergePersonPickerProps) {
  const [search, setSearch] = useState('')
  const [confirmTarget, setConfirmTarget] = useState<Person | null>(null)
  const popoverRef = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()

  const personsQuery = useQuery({
    queryKey: ['persons'],
    queryFn: () => api.getPersons(),
  })

  const mergeMutation = useMutation({
    mutationFn: (intoPersonId: string) => api.mergePerson(sourcePersonId, intoPersonId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['persons'] })
      qc.invalidateQueries({ predicate: (q) => q.queryKey[0] === 'image' && q.queryKey[2] === 'faces' })
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
  const filtered = (search.trim()
    ? persons.filter((p) => p.name.toLowerCase().includes(search.trim().toLowerCase()))
    : persons
  ).filter((p) => p.person_id !== sourcePersonId)

  // Position: to the right of anchor, clamped to viewport
  const POPOVER_W = 260
  const POPOVER_H = 320
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
      {confirmTarget ? (
        /* Confirm view */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 16 }}>
          <div style={{ fontSize: 13, color: '#d0d0d0', lineHeight: 1.5 }}>
            Merge <strong style={{ color: '#fff' }}>{sourcePersonName}</strong> into{' '}
            <strong style={{ color: '#fff' }}>{confirmTarget.name}</strong>?
            <br />
            <span style={{ color: '#999', fontSize: 12 }}>
              This deletes <em>{sourcePersonName}</em> and reassigns its faces.
            </span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => mergeMutation.mutate(confirmTarget.person_id)}
              disabled={mergeMutation.isPending}
              style={{
                flex: 1,
                background: '#3a4a3a',
                border: '1px solid #5a5',
                borderRadius: 4,
                color: '#8d8',
                cursor: 'pointer',
                fontSize: 12,
                padding: '6px 0',
              }}
            >
              {mergeMutation.isPending ? 'Merging…' : 'Confirm'}
            </button>
            <button
              onClick={() => setConfirmTarget(null)}
              disabled={mergeMutation.isPending}
              style={{
                flex: 1,
                background: 'transparent',
                border: '1px solid #555',
                borderRadius: 4,
                color: '#aaa',
                cursor: 'pointer',
                fontSize: 12,
                padding: '6px 0',
              }}
            >
              Back
            </button>
          </div>
          {mergeMutation.isError && (
            <div style={{ fontSize: 11, color: '#f88' }}>Merge failed. Try again.</div>
          )}
        </div>
      ) : (
        /* Picker view */
        <>
          {/* Header */}
          <div style={{ padding: '8px 10px', borderBottom: '1px solid #333', flexShrink: 0 }}>
            <div style={{ fontSize: 11, color: '#888', marginBottom: 6 }}>
              Merge <strong style={{ color: '#bbb' }}>{sourcePersonName}</strong> into…
            </div>
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
            {filtered.map((person) => (
              <button
                key={person.person_id}
                onClick={() => setConfirmTarget(person)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  width: '100%',
                  background: 'transparent',
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
                <span style={{ fontSize: 11, color: '#666', flexShrink: 0, marginLeft: 4 }}>
                  {person.face_count}
                </span>
              </button>
            ))}
            {!personsQuery.isLoading && filtered.length === 0 && (
              <div style={{ color: '#666', fontSize: 12, padding: '8px 10px' }}>No other persons</div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
