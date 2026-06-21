import { useState } from 'react'
import type { GalleryImage } from '../api/client'

interface ThumbnailCellProps {
  image: GalleryImage
  isSelected: boolean
  onClick: () => void
  cellRef?: (el: HTMLDivElement | null) => void
}

export default function ThumbnailCell({ image, isSelected, onClick, cellRef }: ThumbnailCellProps) {
  const [isFocused, setIsFocused] = useState(false)
  const isPickDecision = image.decision === 'pick'
  const isRejectDecision = image.decision === 'reject'

  const filename = image.path.split('/').pop() ?? image.image_id

  let boxShadow = 'none'
  if (isSelected) {
    boxShadow = '0 0 0 3px #f90'
  } else if (isPickDecision) {
    boxShadow = '0 0 0 3px #0f0'
  }

  return (
    <div
      ref={cellRef}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
      style={{
        position: 'relative',
        aspectRatio: '1',
        overflow: 'hidden',
        cursor: 'pointer',
        boxShadow,
        borderRadius: 2,
        outline: isFocused ? '2px solid #5af' : 'none',
        outlineOffset: '-2px',
      }}
    >
      {image.thumbnail_path ? (
        <img
          src={image.thumbnail_path}
          alt={filename}
          loading="lazy"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            display: 'block',
            opacity: isRejectDecision ? 0.4 : 1,
            transition: 'opacity 0.1s',
          }}
        />
      ) : (
        <div
          style={{
            width: '100%',
            height: '100%',
            background: '#2a2a2a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 4,
          }}
        >
          <span
            style={{
              fontSize: 10,
              color: '#666',
              wordBreak: 'break-all',
              textAlign: 'center',
              lineHeight: 1.3,
              opacity: isRejectDecision ? 0.4 : 1,
            }}
          >
            {filename}
          </span>
        </div>
      )}

      {/* Reject tint overlay */}
      {isRejectDecision && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(255, 68, 68, 0.4)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Decision badge */}
      {image.decision && (
        <div
          style={{
            position: 'absolute',
            top: 4,
            right: 4,
            fontSize: 10,
            fontWeight: 700,
            padding: '1px 5px',
            borderRadius: 3,
            background: isPickDecision ? '#0f0' : '#ff4444',
            color: isPickDecision ? '#000' : '#fff',
            pointerEvents: 'none',
            textTransform: 'uppercase',
          }}
        >
          {image.decision}
        </div>
      )}
    </div>
  )
}
