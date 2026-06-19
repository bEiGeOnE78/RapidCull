import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from './api/client'
import GallerySelector from './components/GallerySelector'
import ThumbnailGrid from './components/ThumbnailGrid'
import ImageViewer from './components/ImageViewer'

const PAGE_SIZE = 50

export default function App() {
  const [activeGalleryId, setActiveGalleryId] = useState<string | null>(null)
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null)
  const [gallerySidebarOpen, setGallerySidebarOpen] = useState(true)
  const [page, setPage] = useState(1)

  // Fetch galleries
  const galleriesQuery = useQuery({
    queryKey: ['galleries'],
    queryFn: () => api.getGalleries(),
  })

  // Auto-select first gallery when galleries load
  useEffect(() => {
    if (galleriesQuery.data && galleriesQuery.data.galleries.length > 0 && !activeGalleryId) {
      setActiveGalleryId(galleriesQuery.data.galleries[0].gallery_id)
    }
  }, [galleriesQuery.data, activeGalleryId])

  // Reset page when gallery changes
  useEffect(() => {
    setPage(1)
    setSelectedImageId(null)
  }, [activeGalleryId])

  // Fetch gallery images
  const imagesQuery = useQuery({
    queryKey: ['gallery-images', activeGalleryId, page],
    queryFn: () => api.getGalleryImages(activeGalleryId!, page, PAGE_SIZE),
    enabled: activeGalleryId !== null,
  })

  // Toggle gallery sidebar with G key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement
      // Don't intercept key events in inputs/textareas
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return

      if (e.key === 'g' || e.key === 'G') {
        setGallerySidebarOpen((prev) => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const galleries = galleriesQuery.data?.galleries ?? []
  const images = imagesQuery.data?.images ?? []
  const totalCount = imagesQuery.data?.total ?? 0

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        height: '100vh',
        background: '#181818',
        color: '#e0e0e0',
        overflow: 'hidden',
      }}
    >
      {selectedImageId && (
        <ImageViewer
          imageId={selectedImageId}
          images={images}
          onClose={() => setSelectedImageId(null)}
          onNavigate={(id) => setSelectedImageId(id)}
        />
      )}
      <GallerySelector
        galleries={galleries}
        activeGalleryId={activeGalleryId}
        onSelect={(id) => setActiveGalleryId(id)}
        isOpen={gallerySidebarOpen}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 16px',
            borderBottom: '1px solid #333',
            background: '#1e1e1e',
            flexShrink: 0,
          }}
        >
          <button
            onClick={() => setGallerySidebarOpen((prev) => !prev)}
            title="Toggle gallery sidebar (G)"
            style={{
              background: 'transparent',
              border: '1px solid #444',
              color: '#aaa',
              borderRadius: 4,
              padding: '4px 10px',
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            {gallerySidebarOpen ? '◀ Galleries' : '▶ Galleries'}
          </button>
          <span style={{ color: '#888', fontSize: 13 }}>
            {activeGalleryId
              ? galleries.find((g) => g.gallery_id === activeGalleryId)?.name ?? activeGalleryId
              : 'No gallery selected'}
          </span>
          {galleriesQuery.isLoading && (
            <span style={{ color: '#555', fontSize: 12, marginLeft: 'auto' }}>Loading galleries...</span>
          )}
          {galleriesQuery.isError && (
            <span style={{ color: '#f44', fontSize: 12, marginLeft: 'auto' }}>
              Failed to load galleries
            </span>
          )}
        </div>

        {/* Main content */}
        {activeGalleryId ? (
          <ThumbnailGrid
            images={images}
            selectedImageId={selectedImageId}
            onSelect={(id) => setSelectedImageId(id)}
            isLoading={imagesQuery.isLoading}
            totalCount={totalCount}
            page={page}
            pageSize={PAGE_SIZE}
            onPageChange={(p) => setPage(p)}
          />
        ) : (
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
            {galleriesQuery.isLoading ? 'Loading...' : 'Select a gallery to browse images'}
          </div>
        )}
      </div>
    </div>
  )
}
