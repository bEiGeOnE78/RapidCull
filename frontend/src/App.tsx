import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api/client'
import type { Gallery, ApiError } from './api/client'
import GallerySelector from './components/GallerySelector'
import ThumbnailGrid, { sortImages } from './components/ThumbnailGrid'
import ImageViewer from './components/ImageViewer'
import CommandPalette from './components/CommandPalette'
import JobProgressPanel from './components/JobProgressPanel'
import PersonPanel from './components/PersonPanel'
import TrashPanel from './components/TrashPanel'
import SearchBar from './components/SearchBar'
import SaveAsNewGalleryDialog from './components/SaveAsNewGalleryDialog'
import AddToExistingGalleryDialog from './components/AddToExistingGalleryDialog'
import { useKeyboard } from './hooks/useKeyboard'
import type { SortOrder } from './components/SortControl'

const PAGE_SIZE = 50

export default function App() {
  const qc = useQueryClient()
  const [activeGalleryId, setActiveGalleryId] = useState<string | null>(null)
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null)
  const [gallerySidebarOpen, setGallerySidebarOpen] = useState(true)
  const [page, setPage] = useState(1)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [activeJobLabel, setActiveJobLabel] = useState('')
  const [activeJobOp, setActiveJobOp] = useState('')
  const [personPanelOpen, setPersonPanelOpen] = useState(false)
  const [trashPanelOpen, setTrashPanelOpen] = useState(false)
  const [sortOrder, setSortOrder] = useState<SortOrder>('filename')

  // Search state
  const [searchQuery, setSearchQuery] = useState<string | null>(null)
  const [searchCount, setSearchCount] = useState<number | null>(null)
  const prevGalleryIdRef = useRef<string | null>(null)

  // Multi-select state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [selectionMode, setSelectionMode] = useState(false)
  const [saveAsNewOpen, setSaveAsNewOpen] = useState(false)
  const [addToExistingOpen, setAddToExistingOpen] = useState(false)

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

  // Fetch gallery images (normal)
  const imagesQuery = useQuery({
    queryKey: ['gallery-images', activeGalleryId, page],
    queryFn: () => api.getGalleryImages(activeGalleryId!, page, PAGE_SIZE),
    enabled: activeGalleryId !== null && activeGalleryId !== 'virtual:search',
  })

  // Search images query
  const searchQuery_ = searchQuery ?? ''
  const searchImagesQuery = useQuery({
    queryKey: ['search', searchQuery_, page],
    queryFn: () => api.searchImages(searchQuery_, (page - 1) * PAGE_SIZE, PAGE_SIZE),
    enabled: activeGalleryId === 'virtual:search' && !!searchQuery_,
    retry: (failureCount, error) => {
      // Never retry client errors (4xx) — they are deterministic
      const apiErr = error as ApiError | null
      if (apiErr && typeof apiErr.status === 'number' && apiErr.status >= 400 && apiErr.status < 500) {
        return false
      }
      return failureCount < 1
    },
  })

  // Keep searchCount in sync with search results
  useEffect(() => {
    if (searchImagesQuery.data) {
      setSearchCount(searchImagesQuery.data.total_count)
    }
  }, [searchImagesQuery.data])

  const handleJobStarted = useCallback((jobId: string, label: string, op: string) => {
    setActiveJobId(jobId)
    setActiveJobLabel(label)
    setActiveJobOp(op)
    setCommandPaletteOpen(false)
  }, [])

  const handleSearchSubmit = (q: string) => {
    prevGalleryIdRef.current = activeGalleryId !== 'virtual:search' ? activeGalleryId : prevGalleryIdRef.current
    setSearchQuery(q)
    setActiveGalleryId('virtual:search')
    setSelectionMode(true)
    setSelectedIds(new Set())
    setPage(1)
  }

  const handleSearchClear = () => {
    setSearchQuery(null)
    setSearchCount(null)
    setActiveGalleryId(prevGalleryIdRef.current)
    setSelectionMode(false)
    setSelectedIds(new Set())
    setPage(1)
  }

  const handleSaveAsNew = async (name: string) => {
    try {
      await api.createUserGalleryWithImages(name, Array.from(selectedIds))
      void qc.invalidateQueries({ queryKey: ['galleries'] })
      setSaveAsNewOpen(false)
    } catch (err) {
      console.error('Failed to create gallery:', err)
    }
  }

  const handleAddToExisting = async (gallery: Gallery) => {
    try {
      await api.addImagesToGallery(gallery.gallery_id, Array.from(selectedIds))
      void qc.invalidateQueries({ queryKey: ['galleries'] })
      void qc.invalidateQueries({ queryKey: ['gallery-images', gallery.gallery_id] })
      setAddToExistingOpen(false)
    } catch (err) {
      console.error('Failed to add images to gallery:', err)
    }
  }

  // Global keyboard shortcuts (skipped when focus is in input/textarea/select)
  useKeyboard({
    g: () => setGallerySidebarOpen((prev) => !prev),
    G: () => setGallerySidebarOpen((prev) => !prev),
    '/': () => setCommandPaletteOpen(true),
  })

  const galleries = galleriesQuery.data?.galleries ?? []

  const isSearchView = activeGalleryId === 'virtual:search'
  const images = isSearchView
    ? (searchImagesQuery.data?.images ?? [])
    : (imagesQuery.data?.images ?? [])
  const sortedImages = sortImages(images, sortOrder)
  const totalCount = isSearchView
    ? (searchImagesQuery.data?.total_count ?? 0)
    : (imagesQuery.data?.total ?? 0)
  const isLoading = isSearchView ? searchImagesQuery.isLoading : imagesQuery.isLoading
  const searchError =
    isSearchView && searchImagesQuery.isError ? (searchImagesQuery.error as ApiError) : null

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
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onJobStarted={handleJobStarted}
        activeGalleryId={activeGalleryId}
      />
      <PersonPanel isOpen={personPanelOpen} onClose={() => setPersonPanelOpen(false)} onJobStarted={handleJobStarted} />
      <TrashPanel isOpen={trashPanelOpen} onClose={() => setTrashPanelOpen(false)} />
      {activeJobId !== null && (
        <JobProgressPanel
          jobId={activeJobId}
          label={activeJobLabel}
          op={activeJobOp}
          activeGalleryId={activeGalleryId}
          onClose={() => setActiveJobId(null)}
        />
      )}
      {selectedImageId && (
        <ImageViewer
          imageId={selectedImageId}
          images={sortedImages}
          onClose={() => setSelectedImageId(null)}
          onNavigate={(id) => setSelectedImageId(id)}
        />
      )}
      {saveAsNewOpen && (
        <SaveAsNewGalleryDialog
          count={selectedIds.size}
          onSave={(name) => void handleSaveAsNew(name)}
          onCancel={() => setSaveAsNewOpen(false)}
        />
      )}
      {addToExistingOpen && (
        <AddToExistingGalleryDialog
          count={selectedIds.size}
          onPick={(gallery) => void handleAddToExisting(gallery)}
          onCancel={() => setAddToExistingOpen(false)}
        />
      )}
      <GallerySelector
        galleries={galleries}
        activeGalleryId={activeGalleryId}
        onSelect={(id) => setActiveGalleryId(id)}
        isOpen={gallerySidebarOpen}
        searchQuery={searchQuery}
        searchCount={searchCount}
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
          <span style={{ color: '#888', fontSize: 13, flexShrink: 0 }}>
            {activeGalleryId && activeGalleryId !== 'virtual:search'
              ? galleries.find((g) => g.gallery_id === activeGalleryId)?.name ?? activeGalleryId
              : activeGalleryId === 'virtual:search'
              ? `Search: ${searchQuery}`
              : 'No gallery selected'}
          </span>

          <SearchBar
            currentQuery={searchQuery ?? ''}
            onSubmit={handleSearchSubmit}
            onClear={handleSearchClear}
          />

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            {galleriesQuery.isLoading && (
              <span style={{ color: '#555', fontSize: 12 }}>Loading galleries...</span>
            )}
            {galleriesQuery.isError && (
              <span style={{ color: '#f44', fontSize: 12 }}>Failed to load galleries</span>
            )}
            <button
              onClick={() => setPersonPanelOpen(true)}
              title="People"
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
              People
            </button>
            <button
              onClick={() => setTrashPanelOpen(true)}
              title="Trash"
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
              Trash
            </button>
          </div>
        </div>

        {/* Search error banner */}
        {searchError && (
          <div
            style={{
              background: '#4a1a1a',
              borderBottom: '1px solid #7a2a2a',
              color: '#ffaaaa',
              padding: '8px 16px',
              flexShrink: 0,
              fontSize: 13,
            }}
          >
            <span style={{ fontWeight: 600 }}>Search error: </span>
            {searchError.apiMessage ?? searchError.message}
            {searchError.suggestions && searchError.suggestions.length > 0 && (
              <span style={{ color: '#cc8888', fontSize: 12, marginLeft: 8 }}>
                — Try: {searchError.suggestions.join(', ')}
              </span>
            )}
          </div>
        )}

        {/* Main content */}
        {activeGalleryId ? (
          <ThumbnailGrid
            images={images}
            selectedImageId={selectedImageId}
            onSelect={(id) => setSelectedImageId(id)}
            isLoading={isLoading}
            totalCount={totalCount}
            page={page}
            pageSize={PAGE_SIZE}
            onPageChange={(p) => setPage(p)}
            sortOrder={sortOrder}
            onSortChange={setSortOrder}
            selectionMode={selectionMode}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            onSaveAsNewGallery={() => setSaveAsNewOpen(true)}
            onAddToExisting={() => setAddToExistingOpen(true)}
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
