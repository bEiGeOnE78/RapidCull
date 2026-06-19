import type { GalleryImage } from '../api/client'
import ThumbnailCell from './ThumbnailCell'

interface ThumbnailGridProps {
  images: GalleryImage[]
  selectedImageId: string | null
  onSelect: (imageId: string) => void
  isLoading: boolean
  totalCount: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
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
}: ThumbnailGridProps) {
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
      {/* Scrollable grid area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 4 }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
            gap: 4,
          }}
        >
          {images.map((image) => (
            <ThumbnailCell
              key={image.image_id}
              image={image}
              isSelected={image.image_id === selectedImageId}
              onClick={() => onSelect(image.image_id)}
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
