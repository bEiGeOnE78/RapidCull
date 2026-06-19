import { useCallback, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { GalleryImage } from '../api/client'
import { useKeyboard } from '../hooks/useKeyboard'
import StatusDot from './StatusDot'
import MetadataSidebar from './MetadataSidebar'
import FaceOverlay from './FaceOverlay'

interface ImageViewerProps {
  imageId: string
  images: GalleryImage[]
  onClose: () => void
  onNavigate: (imageId: string) => void
}

export default function ImageViewer({ imageId, images, onClose, onNavigate }: ImageViewerProps) {
  const queryClient = useQueryClient()
  const [zoomMode, setZoomMode] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [metaSidebarOpen, setMetaSidebarOpen] = useState(false)
  const [faceOverlayVisible, setFaceOverlayVisible] = useState(false)

  // Image natural dimensions (from onLoad)
  const [naturalWidth, setNaturalWidth] = useState(0)
  const [naturalHeight, setNaturalHeight] = useState(0)
  // Displayed dimensions (from getBoundingClientRect on load)
  const [displayWidth, setDisplayWidth] = useState(0)
  const [displayHeight, setDisplayHeight] = useState(0)

  const dragStart = useRef<{ x: number; y: number; scrollLeft: number; scrollTop: number } | null>(
    null,
  )
  const scrollRef = useRef<HTMLDivElement>(null)
  const imgRef = useRef<HTMLImageElement>(null)

  const imageQuery = useQuery({
    queryKey: ['image', imageId],
    queryFn: () => api.getImage(imageId),
  })

  const decisionQuery = useQuery({
    queryKey: ['decision', imageId],
    queryFn: () => api.getDecision(imageId),
  })

  const personsQuery = useQuery({
    queryKey: ['persons'],
    queryFn: () => api.getPersons(),
  })

  const invalidateDecision = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['decision', imageId] })
    queryClient.invalidateQueries({ queryKey: ['image', imageId] })
  }, [queryClient, imageId])

  const setDecisionMutation = useMutation({
    mutationFn: (decision: 'pick' | 'reject') => api.setDecision(imageId, decision),
    onSuccess: invalidateDecision,
  })

  const deleteDecisionMutation = useMutation({
    mutationFn: () => api.deleteDecision(imageId),
    onSuccess: invalidateDecision,
  })

  const currentIndex = images.findIndex((img) => img.image_id === imageId)
  const prevImage = currentIndex > 0 ? images[currentIndex - 1] : null
  const nextImage = currentIndex < images.length - 1 ? images[currentIndex + 1] : null

  const decision = decisionQuery.data?.decision ?? imageQuery.data?.decision ?? null

  const handlePick = useCallback(() => {
    if (decision === 'pick') {
      deleteDecisionMutation.mutate()
    } else {
      setDecisionMutation.mutate('pick')
    }
  }, [decision, deleteDecisionMutation, setDecisionMutation])

  const handleReject = useCallback(() => {
    if (decision === 'reject') {
      deleteDecisionMutation.mutate()
    } else {
      setDecisionMutation.mutate('reject')
    }
  }, [decision, deleteDecisionMutation, setDecisionMutation])

  const handleUndo = useCallback(() => {
    deleteDecisionMutation.mutate()
  }, [deleteDecisionMutation])

  const keyMap = useCallback(
    () => ({
      ArrowLeft: () => prevImage && onNavigate(prevImage.image_id),
      ArrowRight: () => nextImage && onNavigate(nextImage.image_id),
      p: () => handlePick(),
      P: () => handlePick(),
      x: () => handleReject(),
      X: () => handleReject(),
      q: () => onClose(),
      Q: () => onClose(),
      Escape: () => onClose(),
      m: () => setMetaSidebarOpen((prev) => !prev),
      M: () => setMetaSidebarOpen((prev) => !prev),
      o: () => setFaceOverlayVisible((prev) => !prev),
      O: () => setFaceOverlayVisible((prev) => !prev),
      ' ': (e: KeyboardEvent) => {
        e.preventDefault()
        setZoomMode((prev) => !prev)
      },
    }),
    [prevImage, nextImage, onNavigate, handlePick, handleReject, onClose],
  )

  useKeyboard(keyMap(), true)

  const imageData = imageQuery.data
  const filename = imageData
    ? imageData.path.split('/').pop() ?? imageData.path
    : imageId

  // Proxy path construction
  const imageSrc = `/proxies/${imageId}/display.jpg`

  // Decision styling
  const containerBorderStyle =
    decision === 'pick'
      ? '2px solid #00ff00'
      : decision === 'reject'
        ? '2px solid #ff4444'
        : '2px solid transparent'

  // Mouse drag handlers for zoom/pan
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!zoomMode || !scrollRef.current) return
    setIsDragging(true)
    dragStart.current = {
      x: e.clientX,
      y: e.clientY,
      scrollLeft: scrollRef.current.scrollLeft,
      scrollTop: scrollRef.current.scrollTop,
    }
    e.preventDefault()
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !dragStart.current || !scrollRef.current) return
    const dx = e.clientX - dragStart.current.x
    const dy = e.clientY - dragStart.current.y
    scrollRef.current.scrollLeft = dragStart.current.scrollLeft - dx
    scrollRef.current.scrollTop = dragStart.current.scrollTop - dy
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    dragStart.current = null
  }

  const handleImageLoad = () => {
    if (!imgRef.current) return
    setNaturalWidth(imgRef.current.naturalWidth)
    setNaturalHeight(imgRef.current.naturalHeight)
    const rect = imgRef.current.getBoundingClientRect()
    setDisplayWidth(rect.width)
    setDisplayHeight(rect.height)
  }

  const persons = personsQuery.data?.persons ?? []

  const btnStyle: React.CSSProperties = {
    background: '#2a2a2a',
    border: '1px solid #444',
    color: '#ccc',
    borderRadius: 4,
    padding: '5px 14px',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
  }

  const pickBtnStyle: React.CSSProperties = {
    ...btnStyle,
    background: decision === 'pick' ? '#1a4a1a' : '#2a2a2a',
    border: decision === 'pick' ? '1px solid #0f0' : '1px solid #444',
    color: decision === 'pick' ? '#0f0' : '#ccc',
  }

  const rejectBtnStyle: React.CSSProperties = {
    ...btnStyle,
    background: decision === 'reject' ? '#4a1a1a' : '#2a2a2a',
    border: decision === 'reject' ? '1px solid #f44' : '1px solid #444',
    color: decision === 'reject' ? '#f44' : '#ccc',
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        background: '#181818',
        display: 'flex',
        flexDirection: 'column',
        color: '#e0e0e0',
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '8px 16px',
          borderBottom: '1px solid #333',
          background: '#1e1e1e',
          flexShrink: 0,
        }}
      >
        <button onClick={onClose} style={btnStyle} title="Close viewer (Q / Esc)">
          ← Back
        </button>

        <span
          style={{
            flex: 1,
            fontSize: 14,
            color: '#ccc',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {filename}
        </span>

        <StatusDot decision={decision} />

        <button onClick={handlePick} style={pickBtnStyle} title="Pick (P)">
          PICK
        </button>
        <button onClick={handleReject} style={rejectBtnStyle} title="Reject (X)">
          REJECT
        </button>
        <button onClick={handleUndo} style={btnStyle} title="Undo decision" disabled={!decision}>
          UNDO
        </button>

        <button
          onClick={() => setZoomMode((prev) => !prev)}
          style={{ ...btnStyle, color: zoomMode ? '#adf' : '#ccc' }}
          title="Toggle zoom (Space)"
        >
          {zoomMode ? 'Zoom' : 'Fit'}
        </button>

        <button
          onClick={() => setFaceOverlayVisible((prev) => !prev)}
          style={{ ...btnStyle, color: faceOverlayVisible ? '#f80' : '#ccc' }}
          title="Toggle face overlay (O)"
        >
          Faces
        </button>

        <button
          onClick={() => setMetaSidebarOpen((prev) => !prev)}
          style={{ ...btnStyle, color: metaSidebarOpen ? '#adf' : '#ccc' }}
          title="Toggle metadata sidebar (M)"
        >
          {metaSidebarOpen ? 'Info ▶' : 'Info ◀'}
        </button>
      </div>

      {/* Image area + metadata sidebar */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>
        {/* Image panel */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden', display: 'flex' }}>
          {/* Scrollable container for zoom mode */}
          <div
            ref={scrollRef}
            style={{
              flex: 1,
              overflow: zoomMode ? 'auto' : 'hidden',
              display: 'flex',
              alignItems: zoomMode ? 'flex-start' : 'center',
              justifyContent: zoomMode ? 'flex-start' : 'center',
              cursor: zoomMode ? (isDragging ? 'grabbing' : 'grab') : 'default',
              userSelect: 'none',
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Image container with decision border */}
            <div
              style={{
                position: 'relative',
                border: containerBorderStyle,
                borderRadius: 2,
                display: 'inline-flex',
                flexShrink: 0,
                maxWidth: zoomMode ? 'none' : '100%',
                maxHeight: zoomMode ? 'none' : '100%',
              }}
            >
              {/* Reject overlay */}
              {decision === 'reject' && (
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'rgba(255,68,68,0.3)',
                    pointerEvents: 'none',
                    zIndex: 1,
                  }}
                />
              )}

              {imageQuery.isLoading ? (
                <div
                  style={{
                    width: 400,
                    height: 300,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#555',
                    fontSize: 14,
                  }}
                >
                  Loading...
                </div>
              ) : (
                <>
                  <img
                    ref={imgRef}
                    src={imageSrc}
                    alt={filename}
                    draggable={false}
                    onLoad={handleImageLoad}
                    onError={(e) => {
                      // Fallback to original path if proxy doesn't exist
                      if (imageData?.path) {
                        const target = e.currentTarget
                        if (target.src !== imageData.path) {
                          target.src = imageData.path
                        }
                      }
                    }}
                    style={{
                      display: 'block',
                      maxWidth: zoomMode ? 'none' : '100%',
                      maxHeight: zoomMode ? 'none' : 'calc(100vh - 100px)',
                      objectFit: zoomMode ? 'none' : 'contain',
                      imageRendering: zoomMode ? 'pixelated' : 'auto',
                      userSelect: 'none',
                      pointerEvents: 'none',
                    }}
                  />
                  <FaceOverlay
                    imageId={imageId}
                    imageNaturalWidth={naturalWidth}
                    imageNaturalHeight={naturalHeight}
                    displayWidth={displayWidth}
                    displayHeight={displayHeight}
                    isVisible={faceOverlayVisible}
                    persons={persons}
                  />
                </>
              )}
            </div>
          </div>

          {/* Prev arrow */}
          {prevImage && (
            <button
              onClick={() => onNavigate(prevImage.image_id)}
              title="Previous image (←)"
              style={{
                position: 'absolute',
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'rgba(0,0,0,0.5)',
                border: '1px solid #444',
                color: '#ccc',
                borderRadius: 4,
                padding: '10px 14px',
                cursor: 'pointer',
                fontSize: 18,
                zIndex: 10,
              }}
            >
              ◄
            </button>
          )}

          {/* Next arrow */}
          {nextImage && (
            <button
              onClick={() => onNavigate(nextImage.image_id)}
              title="Next image (→)"
              style={{
                position: 'absolute',
                right: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'rgba(0,0,0,0.5)',
                border: '1px solid #444',
                color: '#ccc',
                borderRadius: 4,
                padding: '10px 14px',
                cursor: 'pointer',
                fontSize: 18,
                zIndex: 10,
              }}
            >
              ►
            </button>
          )}
        </div>

        {/* Metadata sidebar */}
        <MetadataSidebar imageData={imageData} isOpen={metaSidebarOpen} />
      </div>

      {/* Status bar */}
      <div
        style={{
          padding: '4px 16px',
          borderTop: '1px solid #333',
          background: '#1a1a1a',
          fontSize: 12,
          color: '#666',
          display: 'flex',
          gap: 16,
          flexShrink: 0,
        }}
      >
        <span>
          {currentIndex + 1} / {images.length}
        </span>
        <span>{zoomMode ? 'Zoom mode' : 'Fit mode'} — Space to toggle</span>
        <span>P: pick · X: reject · ←→: navigate · M: metadata · O: faces · Q/Esc: close</span>
      </div>
    </div>
  )
}
