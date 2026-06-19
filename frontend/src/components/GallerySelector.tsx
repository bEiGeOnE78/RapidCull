import type { Gallery } from '../api/client'

interface GallerySelectorProps {
  galleries: Gallery[]
  activeGalleryId: string | null
  onSelect: (galleryId: string) => void
  isOpen: boolean
}

export default function GallerySelector({
  galleries,
  activeGalleryId,
  onSelect,
  isOpen,
}: GallerySelectorProps) {
  if (!isOpen) return null

  return (
    <aside
      style={{
        width: 240,
        minWidth: 240,
        background: '#222',
        borderRight: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        height: '100%',
      }}
    >
      <div
        style={{
          padding: '12px 16px',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#888',
          borderBottom: '1px solid #333',
        }}
      >
        Galleries
      </div>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, flex: 1 }}>
        {galleries.map((gallery) => {
          const isActive = gallery.gallery_id === activeGalleryId
          return (
            <li key={gallery.gallery_id}>
              <button
                onClick={() => onSelect(gallery.gallery_id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  padding: '10px 16px',
                  background: isActive ? '#2a2a2a' : 'transparent',
                  border: 'none',
                  borderLeft: isActive ? '3px solid #4a9eff' : '3px solid transparent',
                  color: isActive ? '#fff' : '#ccc',
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontSize: 13,
                  transition: 'background 0.1s',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    ;(e.currentTarget as HTMLButtonElement).style.background = '#282828'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  }
                }}
              >
                <span
                  style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flex: 1,
                    marginRight: 8,
                  }}
                  title={gallery.name}
                >
                  {gallery.name}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    background: '#333',
                    color: '#aaa',
                    borderRadius: 10,
                    padding: '1px 7px',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  {gallery.image_count}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
      {galleries.length === 0 && (
        <div
          style={{
            padding: '24px 16px',
            color: '#666',
            fontSize: 13,
            textAlign: 'center',
          }}
        >
          No galleries found
        </div>
      )}
    </aside>
  )
}
