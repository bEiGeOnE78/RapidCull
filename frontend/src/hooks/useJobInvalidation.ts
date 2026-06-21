import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export function useJobInvalidation() {
  const qc = useQueryClient()
  return useCallback((op: string, galleryId?: string) => {
    const map: Record<string, () => void> = {
      create_gallery_picks: () => qc.invalidateQueries({ queryKey: ['galleries'] }),
      create_gallery_rejects: () => qc.invalidateQueries({ queryKey: ['galleries'] }),
      move_rejects_to_trash: () => {
        qc.invalidateQueries({ queryKey: ['galleries'] })
        if (galleryId) qc.invalidateQueries({ queryKey: ['gallery-images', galleryId] })
      },
      hard_delete_trash: () => {
        qc.invalidateQueries({ queryKey: ['galleries'] })
        qc.invalidateQueries({ queryKey: ['gallery-images'] })
      },
      ingest: () => qc.invalidateQueries({ queryKey: ['galleries'] }),
      ingest_and_proxy: () => qc.invalidateQueries({ queryKey: ['galleries'] }),
      rebuild_galleries_index: () => qc.invalidateQueries({ queryKey: ['galleries'] }),
    }
    map[op]?.()
  }, [qc])
}
