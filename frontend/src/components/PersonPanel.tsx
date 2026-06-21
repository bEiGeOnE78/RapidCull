import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Person } from '../api/client'
import MergePersonPicker from './MergePersonPicker'

interface PersonPanelProps {
  isOpen: boolean
  onClose: () => void
}

export default function PersonPanel({ isOpen, onClose }: PersonPanelProps) {
  const queryClient = useQueryClient()
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [mergeAnchor, setMergeAnchor] = useState<{ person: Person; rect: DOMRect } | null>(null)

  const personsQuery = useQuery({
    queryKey: ['persons'],
    queryFn: () => api.getPersons(),
    enabled: isOpen,
  })

  const renameMutation = useMutation({
    mutationFn: ({ personId, name }: { personId: string; name: string }) =>
      api.renamePerson(personId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      setRenamingId(null)
      setRenameValue('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (personId: string) => api.deletePerson(personId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['persons'] })
    },
  })

  if (!isOpen) return null

  const persons = personsQuery.data?.persons ?? []

  const handleRenameStart = (personId: string, currentName: string) => {
    setRenamingId(personId)
    setRenameValue(currentName)
  }

  const handleRenameSave = (personId: string) => {
    if (renameValue.trim()) {
      renameMutation.mutate({ personId, name: renameValue.trim() })
    }
  }

  const handleRenameCancel = () => {
    setRenamingId(null)
    setRenameValue('')
  }

  const handleMerge = (person: Person, event: React.MouseEvent<HTMLButtonElement>) => {
    setMergeAnchor({ person, rect: event.currentTarget.getBoundingClientRect() })
  }

  const handleDelete = (personId: string) => {
    if (window.confirm('Delete person and unlink faces?')) {
      deleteMutation.mutate(personId)
    }
  }

  const btnStyle: React.CSSProperties = {
    background: 'transparent',
    border: '1px solid #555',
    color: '#aaa',
    borderRadius: 4,
    padding: '2px 8px',
    cursor: 'pointer',
    fontSize: 11,
  }

  const inputStyle: React.CSSProperties = {
    background: '#333',
    border: '1px solid #555',
    color: '#e0e0e0',
    borderRadius: 4,
    padding: '2px 6px',
    fontSize: 13,
  }

  return (
    <>
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
          <span style={{ fontSize: 16, fontWeight: 600, color: '#e0e0e0' }}>People</span>
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
          {personsQuery.isLoading && (
            <div style={{ color: '#888', fontSize: 13 }}>Loading...</div>
          )}
          {!personsQuery.isLoading && persons.length === 0 && (
            <div style={{ color: '#666', fontSize: 13 }}>No persons identified yet.</div>
          )}
          {persons.map((person) => (
            <div
              key={person.person_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 0',
                borderBottom: '1px solid #2a2a2a',
              }}
            >
              {/* Name or inline edit */}
              {/* Thumbnail */}
              <img
                src={api.getPersonThumbnailUrl(person.person_id, person.face_count)}
                width={48}
                height={48}
                style={{ borderRadius: 4, objectFit: 'cover', flexShrink: 0 }}
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }}
                alt=""
              />
              {renamingId === person.person_id ? (
                <>
                  <input
                    style={{ ...inputStyle, flex: 1 }}
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRenameSave(person.person_id)
                      if (e.key === 'Escape') handleRenameCancel()
                    }}
                    autoFocus
                  />
                  <button
                    style={{ ...btnStyle, borderColor: '#5a5', color: '#8d8' }}
                    onClick={() => handleRenameSave(person.person_id)}
                    disabled={renameMutation.isPending}
                  >
                    Save
                  </button>
                  <button style={btnStyle} onClick={handleRenameCancel}>
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <span style={{ flex: 1, fontSize: 13, color: '#d0d0d0' }}>
                    {person.name}
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      color: '#888',
                      background: '#333',
                      borderRadius: 10,
                      padding: '1px 7px',
                    }}
                  >
                    {person.face_count} face{person.face_count !== 1 ? 's' : ''}
                  </span>
                  <button
                    style={btnStyle}
                    onClick={() => handleRenameStart(person.person_id, person.name)}
                  >
                    Rename
                  </button>
                  <button
                    style={btnStyle}
                    onClick={(e) => handleMerge(person, e)}
                  >
                    Merge
                  </button>
                  <button
                    style={{ ...btnStyle, borderColor: '#744', color: '#f88' }}
                    onClick={() => handleDelete(person.person_id)}
                    disabled={deleteMutation.isPending}
                  >
                    Delete
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
    {mergeAnchor && (
      <MergePersonPicker
        sourcePersonId={mergeAnchor.person.person_id}
        sourcePersonName={mergeAnchor.person.name}
        anchorRect={mergeAnchor.rect}
        onClose={() => setMergeAnchor(null)}
      />
    )}
    </>
  )
}
