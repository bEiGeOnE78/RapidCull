interface TouchToolbarProps {
  decision: 'pick' | 'reject' | null
  onPick: () => void
  onReject: () => void
  onUndo: () => void
  onInfo: () => void
}

export default function TouchToolbar({
  decision,
  onPick,
  onReject,
  onUndo,
  onInfo,
}: TouchToolbarProps) {
  const baseBtn: React.CSSProperties = {
    flex: 1,
    minHeight: 44,
    background: 'transparent',
    border: 'none',
    color: '#ccc',
    fontSize: 22,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: 56,
        background: '#1a1a1a',
        borderTop: '1px solid #333',
        display: 'flex',
        flexDirection: 'row',
        zIndex: 100,
      }}
    >
      <button
        style={{
          ...baseBtn,
          color: decision === 'pick' ? '#00cc44' : '#ccc',
          background: decision === 'pick' ? 'rgba(0,200,68,0.12)' : 'transparent',
        }}
        onClick={onPick}
        title="Pick"
        aria-label="Pick"
      >
        ✓
      </button>
      <button
        style={{
          ...baseBtn,
          color: decision === 'reject' ? '#ff4444' : '#ccc',
          background: decision === 'reject' ? 'rgba(255,68,68,0.12)' : 'transparent',
        }}
        onClick={onReject}
        title="Reject"
        aria-label="Reject"
      >
        ✗
      </button>
      <button style={baseBtn} onClick={onUndo} title="Undo" aria-label="Undo">
        ↩
      </button>
      <button style={baseBtn} onClick={onInfo} title="Info" aria-label="Toggle info">
        ℹ
      </button>
    </div>
  )
}
