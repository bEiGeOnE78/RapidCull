import { useState, useEffect, useRef } from 'react'

interface Props {
  isOpen: boolean
  defaultName?: string
  onSubmit: (name: string) => void
  onCancel: () => void
}

export default function GalleryNameDialog({ isOpen, defaultName = '', onSubmit, onCancel }: Props) {
  const [name, setName] = useState(defaultName)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setName(defaultName)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [isOpen, defaultName])

  if (!isOpen) return null

  const handleSubmit = () => {
    const trimmed = name.trim()
    if (!trimmed) return
    onSubmit(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit()
    if (e.key === 'Escape') onCancel()
  }

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
          width: 360,
          boxShadow: '0 24px 64px rgba(0,0,0,0.8)',
        }}
      >
        <div style={{ fontSize: 14, color: '#ccc', marginBottom: 12 }}>Gallery name</div>
        <input
          ref={inputRef}
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. Best shots"
          style={{
            width: '100%',
            background: '#111',
            border: '1px solid #444',
            borderRadius: 4,
            color: '#e0e0e0',
            fontSize: 14,
            padding: '8px 10px',
            boxSizing: 'border-box',
            outline: 'none',
            marginBottom: 16,
          }}
        />
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
            onClick={handleSubmit}
            disabled={!name.trim()}
            style={{
              background: name.trim() ? '#4a9eff' : '#333',
              border: 'none',
              color: name.trim() ? '#fff' : '#666',
              borderRadius: 4,
              padding: '6px 14px',
              cursor: name.trim() ? 'pointer' : 'default',
              fontSize: 13,
            }}
          >
            OK
          </button>
        </div>
      </div>
    </div>
  )
}
