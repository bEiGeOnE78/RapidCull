export type SortOrder =
  | 'date_asc'
  | 'date_desc'
  | 'filename'
  | 'picks_first'
  | 'rejects_first'
  | 'undecided_first'

interface SortControlProps {
  value: SortOrder
  onChange: (order: SortOrder) => void
}

export default function SortControl({ value, onChange }: SortControlProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as SortOrder)}
      style={{
        background: '#333',
        color: '#ccc',
        border: '1px solid #444',
        borderRadius: 4,
        padding: '3px 8px',
        fontSize: 12,
        cursor: 'pointer',
      }}
      title="Sort order"
    >
      <option value="date_asc">Date (oldest first)</option>
      <option value="date_desc">Date (newest first)</option>
      <option value="filename">Filename</option>
      <option value="picks_first">Picks first</option>
      <option value="rejects_first">Rejects first</option>
      <option value="undecided_first">Undecided first</option>
    </select>
  )
}
