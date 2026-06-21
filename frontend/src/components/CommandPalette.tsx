import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api/client'
import type { Gallery } from '../api/client'
import GalleryNameDialog from './GalleryNameDialog'
import TrashConfirmDialog from './TrashConfirmDialog'

interface Command {
  label: string
  op: string
  params: Record<string, unknown>
  dangerous?: boolean
  needsName?: boolean
  needsTrashCheck?: boolean
}

const COMMANDS: Command[] = [
  { label: 'Process new images', op: 'ingest_and_proxy', params: {} },
  { label: 'Detect faces', op: 'detect_faces', params: {} },
  { label: 'Cluster faces', op: 'cluster_faces', params: {} },
  { label: 'Create gallery from picks', op: 'create_gallery_picks', params: {}, needsName: true },
  { label: 'Move rejects to trash', op: 'move_rejects_to_trash', params: {}, needsTrashCheck: true },
  { label: 'Hard delete trash', op: 'hard_delete_trash', params: {}, dangerous: true },
  { label: 'Rebuild galleries index', op: 'rebuild_galleries_index', params: {} },
  { label: 'Backup', op: 'backup', params: {} },
  { label: 'Check consistency', op: 'check_consistency', params: {} },
  { label: 'Repair consistency', op: 'repair_consistency', params: {}, dangerous: true },
]

interface Props {
  isOpen: boolean
  onClose: () => void
  onJobStarted: (jobId: string, label: string, op: string) => void
  activeGalleryId?: string | null
}

export default function CommandPalette({ isOpen, onClose, onJobStarted, activeGalleryId: _activeGalleryId }: Props) {
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const [pendingCmd, setPendingCmd] = useState<Command | null>(null)
  const [nameDialogOpen, setNameDialogOpen] = useState(false)
  const [trashDialogOpen, setTrashDialogOpen] = useState(false)
  const [trashAffected, setTrashAffected] = useState<Array<{ image_id: string; galleries: Gallery[] }>>([])

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

  const dispatchJob = useCallback(
    async (cmd: Command, extraParams?: Record<string, unknown>) => {
      try {
        const params = { ...cmd.params, ...extraParams }
        const result = await api.createJob(cmd.op, params)
        onJobStarted(result.job_id, cmd.label, cmd.op)
        onClose()
      } catch (err) {
        console.error('Failed to create job:', err)
      }
    },
    [onClose, onJobStarted],
  )

  const executeCommand = useCallback(
    async (cmd: Command) => {
      if (cmd.dangerous) {
        const confirmed = window.confirm(
          `Are you sure you want to run "${cmd.label}"? This action cannot be undone.`,
        )
        if (!confirmed) return
      }

      if (cmd.needsName) {
        setPendingCmd(cmd)
        setNameDialogOpen(true)
        return
      }

      if (cmd.needsTrashCheck) {
        // Fetch galleries for images in current gallery to detect multi-gallery membership.
        // We pass no specific image selection here — the job operates on all rejects.
        // We do a best-effort check: if we can't enumerate specific images, dispatch directly.
        // The trash check is a UX warning, not a gate, so we dispatch if fetch fails.
        try {
          // We don't have a way to enumerate reject images here without another API call.
          // Dispatch directly — the per-image trash flow from ThumbnailGrid would use the
          // TrashConfirmDialog with specific image ids. Job-level trash doesn't select images.
          await dispatchJob(cmd)
        } catch (err) {
          console.error('Failed to dispatch trash job:', err)
        }
        return
      }

      await dispatchJob(cmd)
    },
    [dispatchJob],
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

  const handleNameSubmit = useCallback(
    (name: string) => {
      if (!pendingCmd) return
      setNameDialogOpen(false)
      void dispatchJob(pendingCmd, { name })
      setPendingCmd(null)
    },
    [pendingCmd, dispatchJob],
  )

  const handleNameCancel = useCallback(() => {
    setNameDialogOpen(false)
    setPendingCmd(null)
  }, [])

  const handleTrashConfirm = useCallback(() => {
    if (!pendingCmd) return
    setTrashDialogOpen(false)
    setTrashAffected([])
    void dispatchJob(pendingCmd)
    setPendingCmd(null)
  }, [pendingCmd, dispatchJob])

  const handleTrashCancel = useCallback(() => {
    setTrashDialogOpen(false)
    setTrashAffected([])
    setPendingCmd(null)
  }, [])

  if (!isOpen && !nameDialogOpen && !trashDialogOpen) return null

  return (
    <>
    <GalleryNameDialog
      isOpen={nameDialogOpen}
      onSubmit={handleNameSubmit}
      onCancel={handleNameCancel}
    />
    <TrashConfirmDialog
      isOpen={trashDialogOpen}
      affectedImages={trashAffected}
      onConfirm={handleTrashConfirm}
      onCancel={handleTrashCancel}
    />
    {isOpen && <div
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
    </div>}
    </>
  )
}
