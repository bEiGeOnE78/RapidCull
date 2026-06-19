import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api/client'

interface Command {
  label: string
  op: string
  params: Record<string, unknown>
  dangerous?: boolean
}

const COMMANDS: Command[] = [
  { label: 'Process new images', op: 'ingest_and_proxy', params: {} },
  { label: 'Detect faces', op: 'detect_faces', params: {} },
  { label: 'Cluster faces', op: 'cluster_faces', params: {} },
  { label: 'Create gallery from picks', op: 'create_gallery_picks', params: {} },
  { label: 'Move rejects to trash', op: 'move_rejects_to_trash', params: {} },
  { label: 'Hard delete trash', op: 'hard_delete_trash', params: {}, dangerous: true },
  { label: 'Rebuild galleries index', op: 'rebuild_galleries_index', params: {} },
  { label: 'Backup', op: 'backup', params: {} },
  { label: 'Check consistency', op: 'check_consistency', params: {} },
  { label: 'Repair consistency', op: 'repair_consistency', params: {}, dangerous: true },
]

interface Props {
  isOpen: boolean
  onClose: () => void
  onJobStarted: (jobId: string, label: string) => void
}

export default function CommandPalette({ isOpen, onClose, onJobStarted }: Props) {
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const filtered = COMMANDS.filter((cmd) =>
    cmd.label.toLowerCase().includes(search.toLowerCase()),
  )

  // Reset state when opened
  useEffect(() => {
    if (isOpen) {
      setSearch('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [isOpen])

  // Clamp selectedIndex when filter changes
  useEffect(() => {
    setSelectedIndex((prev) => Math.min(prev, Math.max(0, filtered.length - 1)))
  }, [filtered.length])

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return
    const item = listRef.current.children[selectedIndex] as HTMLElement | undefined
    item?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  const executeCommand = useCallback(
    async (cmd: Command) => {
      if (cmd.dangerous) {
        const confirmed = window.confirm(
          `Are you sure you want to run "${cmd.label}"? This action cannot be undone.`,
        )
        if (!confirmed) return
      }
      try {
        const result = await api.createJob(cmd.op, cmd.params)
        onJobStarted(result.job_id, cmd.label)
        onClose()
      } catch (err) {
        console.error('Failed to create job:', err)
      }
    },
    [onClose, onJobStarted],
  )

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!isOpen) return
      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        const cmd = filtered[selectedIndex]
        if (cmd) executeCommand(cmd)
      }
    },
    [isOpen, onClose, filtered, selectedIndex, executeCommand],
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (!isOpen) return null

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(10px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '15vh',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 560,
          maxHeight: 480,
          background: '#222',
          border: '1px solid #444',
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 24px 64px rgba(0,0,0,0.8)',
        }}
      >
        {/* Search input */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #333', background: '#111' }}>
          <input
            ref={inputRef}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setSelectedIndex(0)
            }}
            placeholder="Search commands..."
            style={{
              width: '100%',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#e0e0e0',
              fontSize: 16,
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Command list */}
        <div
          ref={listRef}
          style={{
            overflowY: 'auto',
            flex: 1,
          }}
        >
          {filtered.length === 0 && (
            <div style={{ padding: '24px 16px', color: '#666', fontSize: 13, textAlign: 'center' }}>
              No commands match "{search}"
            </div>
          )}
          {filtered.map((cmd, i) => {
            const isSelected = i === selectedIndex
            return (
              <div
                key={cmd.op}
                onClick={() => executeCommand(cmd)}
                onMouseEnter={() => setSelectedIndex(i)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 16px',
                  cursor: 'pointer',
                  background: isSelected ? '#333' : 'transparent',
                  borderLeft: isSelected ? '2px solid #4af' : '2px solid transparent',
                  transition: 'background 0.1s',
                  color: cmd.dangerous ? '#f88' : '#e0e0e0',
                }}
              >
                <span style={{ width: 16, fontSize: 12, color: '#666', flexShrink: 0 }}>›</span>
                <span style={{ fontSize: 14 }}>{cmd.label}</span>
                {cmd.dangerous && (
                  <span style={{ marginLeft: 'auto', fontSize: 11, color: '#f66', opacity: 0.7 }}>
                    destructive
                  </span>
                )}
              </div>
            )
          })}
        </div>

        {/* Footer hint */}
        <div
          style={{
            padding: '6px 16px',
            borderTop: '1px solid #333',
            display: 'flex',
            gap: 16,
            color: '#555',
            fontSize: 11,
          }}
        >
          <span>↑↓ navigate</span>
          <span>↵ run</span>
          <span>Esc close</span>
        </div>
      </div>
    </div>
  )
}
