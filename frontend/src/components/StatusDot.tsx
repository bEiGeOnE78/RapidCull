interface StatusDotProps {
  decision: 'pick' | 'reject' | null
}

export default function StatusDot({ decision }: StatusDotProps) {
  const color = decision === 'pick' ? '#00ff00' : decision === 'reject' ? '#ff4444' : '#555555'

  return (
    <div
      style={{
        width: 12,
        height: 12,
        borderRadius: '50%',
        background: color,
        flexShrink: 0,
      }}
    />
  )
}
