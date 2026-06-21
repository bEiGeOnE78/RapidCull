import { useState, useEffect } from 'react'

interface Props {
  personName: string
  faceCount: number
  onConfirm: (deleteEmbeddings: boolean) => void
  onCancel: () => void
}

export default function DeletePersonDialog({ personName, faceCount, onConfirm, onCancel }: Props) {
  const [deleteEmbeddings, setDeleteEmbeddings] = useState(false)

  useEffect(() => {
    setDeleteEmbeddings(false)
  }, [personName])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onCancel])

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
          width: 380,
          boxShadow: '0 24px 64px rgba(0,0,0,0.8)',
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 600, color: '#e0e0e0', marginBottom: 12 }}>
          Delete {personName}?
        </div>
        <div style={{ fontSize: 13, color: '#aaa', marginBottom: 16, lineHeight: 1.5 }}>
          {faceCount} face{faceCount !== 1 ? 's' : ''} linked to this person. Face rows will be
          unlinked but kept for re-clustering unless you choose to delete embeddings.
        </div>
        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 13,
            color: '#f88',
            marginBottom: 20,
            cursor: 'pointer',
          }}
        >
          <input
            type="checkbox"
            checked={deleteEmbeddings}
            onChange={(e) => setDeleteEmbeddings(e.target.checked)}
            style={{ cursor: 'pointer' }}
          />
          Also delete embeddings (cannot be undone)
        </label>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
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
            onClick={() => onConfirm(deleteEmbeddings)}
            style={{
              background: '#7a2222',
              border: '1px solid #a33',
              color: '#f88',
              borderRadius: 4,
              padding: '6px 14px',
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
