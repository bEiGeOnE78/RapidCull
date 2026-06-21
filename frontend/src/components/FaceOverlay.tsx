import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Person } from '../api/client'
import FaceAssignPopover from './FaceAssignPopover'

interface FaceOverlayProps {
  imageId: string
  imageNaturalWidth: number
  imageNaturalHeight: number
  displayWidth: number
  displayHeight: number
  isVisible: boolean
  persons: Person[]
}

export default function FaceOverlay({
  imageId,
  imageNaturalWidth,
  imageNaturalHeight,
  displayWidth,
  displayHeight,
  isVisible,
  persons,
}: FaceOverlayProps) {
  const [selectedFaceId, setSelectedFaceId] = useState<string | null>(null)
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null)

  const facesQuery = useQuery({
    queryKey: ['image', imageId, 'faces'],
    queryFn: () => api.getFaces(imageId),
    enabled: isVisible,
  })

  if (!isVisible) return null
  if (!facesQuery.data) return null
  if (imageNaturalWidth === 0 || imageNaturalHeight === 0) return null
  if (displayWidth === 0 || displayHeight === 0) return null

  const scale = Math.min(displayWidth / imageNaturalWidth, displayHeight / imageNaturalHeight)
  const renderedW = imageNaturalWidth * scale
  const renderedH = imageNaturalHeight * scale
  const offsetX = (displayWidth - renderedW) / 2
  const offsetY = (displayHeight - renderedH) / 2

  const selectedFace = selectedFaceId
    ? facesQuery.data.faces.find((f) => f.face_id === selectedFaceId) ?? null
    : null

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 5,
      }}
    >
      {facesQuery.data.faces.map((face) => {
        const left = face.bbox.x * scale + offsetX
        const top = face.bbox.y * scale + offsetY
        const width = face.bbox.w * scale
        const height = face.bbox.h * scale

        const isSelected = face.face_id === selectedFaceId
        const color = isSelected ? '#ffdd44' : face.person_id ? '#44aaff' : '#ff8800'

        const person = face.person_id
          ? persons.find((p) => p.person_id === face.person_id)
          : null
        const label = person?.name ?? face.person_name ?? 'Unknown'

        return (
          <div key={face.face_id}>
            {/* Bounding box — clickable */}
            <div
              style={{
                position: 'absolute',
                left,
                top,
                width,
                height,
                border: `2px solid ${color}`,
                boxSizing: 'border-box',
                cursor: 'pointer',
                pointerEvents: 'auto',
              }}
              onClick={(e) => {
                e.stopPropagation()
                if (isSelected) {
                  setSelectedFaceId(null)
                  setAnchorRect(null)
                } else {
                  setSelectedFaceId(face.face_id)
                  setAnchorRect((e.currentTarget as HTMLElement).getBoundingClientRect())
                }
              }}
            />
            {/* Label below box */}
            <div
              style={{
                position: 'absolute',
                left,
                top: top + height + 2,
                background: 'rgba(0,0,0,0.7)',
                color,
                fontSize: 11,
                padding: '1px 5px',
                whiteSpace: 'nowrap',
                lineHeight: '16px',
                pointerEvents: 'none',
              }}
            >
              {label}
            </div>
          </div>
        )
      })}

      {selectedFace && anchorRect && (
        <FaceAssignPopover
          faceId={selectedFace.face_id}
          currentPersonId={selectedFace.person_id}
          imageId={imageId}
          anchorRect={anchorRect}
          onClose={() => {
            setSelectedFaceId(null)
            setAnchorRect(null)
          }}
        />
      )}
    </div>
  )
}
