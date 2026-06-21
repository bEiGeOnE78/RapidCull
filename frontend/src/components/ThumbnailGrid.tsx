import { useRef, useCallback } from 'react'
import type { GalleryImage } from '../api/client'
import ThumbnailCell from './ThumbnailCell'
import SortControl, { type SortOrder } from './SortControl'

interface ThumbnailGridProps {
  images: GalleryImage[]
  selectedImageId: string | null
  onSelect: (imageId: string) => void
  isLoading: boolean
  totalCount: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  sortOrder: SortOrder
  onSortChange: (order: SortOrder) => void
}

function decisionRank(decision: string | null | undefined, mode: SortOrder): number {
  if (mode === 'picks_first') {
    if (decision === 'pick') return 0
    if (!decision) return 1
    return 2
  }
  if (mode === 'rejects_first') {
    if (decision === 'reject') return 0
    if (!decision) return 1
    return 2
  }
  // undecided_first
  if (!decision) return 0
  if (decision === 'pick') return 1
  return 2
}

export function sortImages(images: GalleryImage[], order: SortOrder): GalleryImage[] {
  const sorted = [...images]
  switch (order) {
    case 'date_asc':
      return sorted.sort((a, b) => a.path.localeCompare(b.path))
    case 'date_desc':
      return sorted.sort((a, b) => b.path.localeCompare(a.path))
    case 'filename':
      return sorted.sort((a, b) => {
        const fa = a.path.split('/').pop() ?? a.path
        const fb = b.path.split('/').pop() ?? b.path
        return fa.localeCompare(fb)
      })
    case 'picks_first':
    case 'rejects_first':
    case 'undecided_first':
      return sorted.sort(
        (a, b) => decisionRank(a.decision, order) - decisionRank(b.decision, order),
      )
    default:
      return sorted
  }
}

export default function ThumbnailGrid({
  images,
  selectedImageId,
  onSelect,
  isLoading,
  totalCount,
  page,
  pageSize,
  onPageChange,
  sortOrder,
  onSortChange,
}: ThumbnailGridProps) {
  const gridRef = useRef<HTMLDivElement>(null)
  const cellRefs = useRef<(HTMLDivElement | null)[]>([])

  const getColumnsPerRow = useCallback(() => {
    if (!gridRef.current) return 7
    return Math.max(1, Math.floor((gridRef.current.offsetWidth + 4) / (130 + 4)))
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) return
    const cells = cellRefs.current
    const idx = cells.findIndex(c => c === document.activeElement)
    if (idx === -1) return
    const cols = getColumnsPerRow()
    let next = idx
    if (e.key === 'ArrowRight') next = Math.min(idx + 1, cells.length - 1)
    else if (e.key === 'ArrowLeft') next = Math.max(idx - 1, 0)
    else if (e.key === 'ArrowDown') next = Math.min(idx + cols, cells.length - 1)
    else if (e.key === 'ArrowUp') next = Math.max(idx - cols, 0)
    if (next !== idx) {
      e.preventDefault()
      cells[next]?.focus()
    }
  }, [getColumnsPerRow])

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize))
  const startItem = totalCount === 0 ? 0 : (page - 1) * pageSize + 1
  const endItem = Math.min(page * pageSize, totalCount)

  if (isLoading) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          fontSize: 14,
        }}
      >
        <span>Loading...</span>
      </div>
    )
  }

  if (images.length === 0 && !isLoading) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#555',
          fontSize: 14,
        }}
      >
        No images in this gallery
      </div>
    )
  }

  const sortedImages = sortImages(images, sortOrder)

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        background: '#181818',
      }}
    >
      {/* Sort header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 8px',
          borderBottom: '1px solid #2a2a2a',
          background: '#1a1a1a',
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 11, color: '#666' }}>Sort:</span>
        <SortControl value={sortOrder} onChange={onSortChange} />
      </div>

      {/* Scrollable grid area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 4 }} onKeyDown={handleKeyDown}>
        <div
          ref={gridRef}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
            gap: 4,
          }}
        >
          {sortedImages.map((image, idx) => (
            <ThumbnailCell
              key={image.image_id}
              image={image}
              isSelected={image.image_id === selectedImageId}
              onClick={() => onSelect(image.image_id)}
              cellRef={(el) => { cellRefs.current[idx] = el }}
            />
          ))}
        </div>
      </div>

      {/* Pagination bar */}
      {totalCount > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            padding: '8px 16px',
            borderTop: '1px solid #333',
            background: '#1e1e1e',
            fontSize: 13,
            color: '#aaa',
            flexShrink: 0,
          }}
        >
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            style={{
              background: page <= 1 ? '#2a2a2a' : '#333',
              border: '1px solid #444',
              color: page <= 1 ? '#555' : '#ccc',
              borderRadius: 4,
              padding: '4px 12px',
              cursor: page <= 1 ? 'default' : 'pointer',
              fontSize: 13,
            }}
          >
            ← Prev
          </button>
          <span>
            {startItem}–{endItem} of {totalCount}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            style={{
              background: page >= totalPages ? '#2a2a2a' : '#333',
              border: '1px solid #444',
              color: page >= totalPages ? '#555' : '#ccc',
              borderRadius: 4,
              padding: '4px 12px',
              cursor: page >= totalPages ? 'default' : 'pointer',
              fontSize: 13,
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
