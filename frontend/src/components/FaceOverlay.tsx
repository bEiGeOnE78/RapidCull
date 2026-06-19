import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Person } from '../api/client'

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
  const facesQuery = useQuery({
    queryKey: ['faces', imageId],
    queryFn: () => api.getFaces(imageId),
    enabled: isVisible,
  })

  if (!isVisible) return null
  if (!facesQuery.data) return null
  if (imageNaturalWidth === 0 || imageNaturalHeight === 0) return null
  if (displayWidth === 0 || displayHeight === 0) return null

  const scaleX = displayWidth / imageNaturalWidth
  const scaleY = displayHeight / imageNaturalHeight

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
        const left = face.bbox_x * scaleX
        const top = face.bbox_y * scaleY
        const width = face.bbox_w * scaleX
        const height = face.bbox_h * scaleY

        const color = face.person_id ? '#44aaff' : '#ff8800'

        const person = face.person_id
          ? persons.find((p) => p.person_id === face.person_id)
          : null
        const label = person ? person.name : 'Unknown'

        return (
          <div key={face.face_id}>
            {/* Bounding box */}
            <div
              style={{
                position: 'absolute',
                left,
                top,
                width,
                height,
                border: `2px solid ${color}`,
                boxSizing: 'border-box',
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
              }}
            >
              {label}
            </div>
          </div>
        )
      })}
    </div>
  )
}
