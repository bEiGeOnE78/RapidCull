import type { ImageData } from '../api/client'

interface MetadataSidebarProps {
  imageData: ImageData | undefined
  isOpen: boolean
}

function getMetaStr(meta: Record<string, unknown>, ...keys: string[]): string {
  for (const key of keys) {
    const val = meta[key]
    if (val !== undefined && val !== null && val !== '') return String(val)
  }
  return ''
}

function formatFStop(raw: string): string {
  const n = parseFloat(raw)
  if (isNaN(n)) return raw
  return `f/${n}`
}

function formatShutter(raw: string): string {
  // ExifTool may give "1/250" or "0.004" or "1/8"
  if (raw.includes('/')) return `${raw}s`
  const n = parseFloat(raw)
  if (isNaN(n)) return raw
  if (n < 1) {
    const denom = Math.round(1 / n)
    return `1/${denom}s`
  }
  return `${n}s`
}

function formatFocalLength(raw: string): string {
  const n = parseFloat(raw)
  if (isNaN(n)) return raw
  return `${n}mm`
}

interface BadgeProps {
  label: string
}

function Badge({ label }: BadgeProps) {
  if (!label) return null
  return (
    <span
      style={{
        background: '#333',
        color: '#ccc',
        fontSize: 11,
        borderRadius: 4,
        padding: '2px 7px',
        whiteSpace: 'nowrap',
        display: 'inline-block',
      }}
    >
      {label}
    </span>
  )
}

interface ExifRowProps {
  label: string
  value: string
}

function ExifRow({ label, value }: ExifRowProps) {
  if (!value) return null
  return (
    <tr>
      <td
        style={{
          color: '#888',
          fontSize: 12,
          paddingRight: 10,
          paddingBottom: 4,
          whiteSpace: 'nowrap',
          verticalAlign: 'top',
        }}
      >
        {label}
      </td>
      <td style={{ color: '#ddd', fontSize: 12, paddingBottom: 4, wordBreak: 'break-word' }}>
        {value}
      </td>
    </tr>
  )
}

export default function MetadataSidebar({ imageData, isOpen }: MetadataSidebarProps) {
  if (!isOpen) return null

  const meta: Record<string, unknown> = imageData?.metadata ?? {}

  // Camera badges
  const fstopRaw = getMetaStr(meta, 'FNumber', 'Aperture')
  const shutterRaw = getMetaStr(meta, 'ShutterSpeedValue', 'ExposureTime')
  const isoRaw = getMetaStr(meta, 'ISO', 'ISOSpeedRatings')
  const focalRaw = getMetaStr(meta, 'FocalLength')
  const widthRaw = getMetaStr(meta, 'ImageWidth')
  const heightRaw = getMetaStr(meta, 'ImageHeight')
  const ext = imageData?.path ? '.' + (imageData.path.split('.').pop()?.toLowerCase() ?? '') : ''

  const fstopBadge = fstopRaw ? formatFStop(fstopRaw) : ''
  const shutterBadge = shutterRaw ? formatShutter(shutterRaw) : ''
  const isoBadge = isoRaw ? `ISO ${isoRaw}` : ''
  const focalBadge = focalRaw ? formatFocalLength(focalRaw) : ''

  let mpBadge = ''
  const w = parseFloat(widthRaw)
  const h = parseFloat(heightRaw)
  if (!isNaN(w) && !isNaN(h) && w > 0 && h > 0) {
    mpBadge = `${((w * h) / 1_000_000).toFixed(1)} MP`
  }

  // EXIF table rows
  const dateTime = getMetaStr(meta, 'DateTimeOriginal', 'DateTime', 'capture_datetime')
  const make = getMetaStr(meta, 'Make', 'camera_make')
  const model = getMetaStr(meta, 'Model', 'camera_model')
  const camera = [make, model].filter(Boolean).join(' ')
  const lens = getMetaStr(meta, 'LensModel')
  const focal35 = getMetaStr(meta, 'FocalLengthIn35mmFormat', 'FocalLengthIn35mmFilm')
  const focal35Str = focal35 ? formatFocalLength(focal35) : ''
  const dims =
    widthRaw && heightRaw && !isNaN(w) && !isNaN(h) ? `${Math.round(w)} × ${Math.round(h)}` : ''

  const hasGPS =
    meta['GPSLatitude'] !== undefined &&
    meta['GPSLatitude'] !== null &&
    meta['GPSLongitude'] !== undefined &&
    meta['GPSLongitude'] !== null

  const faceCount = imageData?.face_count ?? 0

  return (
    <div
      style={{
        width: 280,
        flexShrink: 0,
        background: '#222',
        borderLeft: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        padding: '12px 14px',
        gap: 14,
      }}
    >
      {/* Camera badge row */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
        <Badge label={fstopBadge} />
        <Badge label={shutterBadge} />
        <Badge label={isoBadge} />
        <Badge label={focalBadge} />
        <Badge label={mpBadge} />
        <Badge label={ext} />
      </div>

      {/* EXIF table */}
      <div>
        <div
          style={{ fontSize: 11, color: '#666', textTransform: 'uppercase', marginBottom: 8, letterSpacing: 1 }}
        >
          EXIF
        </div>
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <tbody>
            <ExifRow label="Date" value={dateTime} />
            <ExifRow label="Camera" value={camera} />
            <ExifRow label="Lens" value={lens} />
            <ExifRow label="Focal (35mm)" value={focal35Str} />
            <ExifRow label="Dimensions" value={dims} />
            {hasGPS && (
              <tr>
                <td
                  style={{
                    color: '#888',
                    fontSize: 12,
                    paddingRight: 10,
                    paddingBottom: 4,
                    whiteSpace: 'nowrap',
                    verticalAlign: 'top',
                  }}
                >
                  GPS
                </td>
                <td style={{ fontSize: 12, paddingBottom: 4 }}>
                  <a href="#" style={{ color: '#4af', marginRight: 8 }}>
                    Maps
                  </a>
                  <a href="#" style={{ color: '#4af' }}>
                    OSM
                  </a>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Face section */}
      <div
        style={{
          borderTop: '1px solid #333',
          paddingTop: 10,
          fontSize: 12,
          color: '#888',
        }}
      >
        {faceCount === 0
          ? 'No faces detected'
          : `${faceCount} face${faceCount !== 1 ? 's' : ''} detected`}
      </div>
    </div>
  )
}
