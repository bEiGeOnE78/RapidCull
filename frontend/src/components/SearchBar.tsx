import { useState, useEffect, useRef } from 'react'

interface Props {
  onSubmit: (q: string) => void
  onClear: () => void
  currentQuery: string
}

export default function SearchBar({ onSubmit, onClear, currentQuery }: Props) {
  const [value, setValue] = useState(currentQuery)
  const inputRef = useRef<HTMLInputElement>(null)

  // Sync external clear
  useEffect(() => {
    setValue(currentQuery)
  }, [currentQuery])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const trimmed = value.trim()
      if (trimmed) onSubmit(trimmed)
    } else if (e.key === 'Escape') {
      onClear()
      setValue('')
      inputRef.current?.blur()
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1, maxWidth: 420 }}>
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="person=Maya AND iso>800"
        style={{
          background: '#111',
          border: '1px solid #444',
          borderRadius: 4,
          color: '#e0e0e0',
          fontSize: 13,
          padding: '5px 10px',
          outline: 'none',
          width: '100%',
          boxSizing: 'border-box',
        }}
      />
      <span style={{ fontSize: 10, color: '#555', paddingLeft: 2 }}>
        Fields: person date camera lens iso fnumber focal keyword
      </span>
    </div>
  )
}
