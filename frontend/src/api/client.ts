const BASE = '/api/v1'

export interface ApiResponse<T> {
  ok: boolean
  data: T
  meta: Record<string, unknown>
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  const body: ApiResponse<T> = await res.json()
  if (!body.ok) throw new Error(String((body as unknown as { detail: unknown }).detail ?? 'API error'))
  return body.data
}

export const api = {
  getGalleries: () => request<GalleriesData>('/galleries'),
  getGalleryImages: (galleryId: string, page = 1, pageSize = 50) =>
    request<GalleryImagesData>(`/galleries/${encodeURIComponent(galleryId)}/images?page=${page}&page_size=${pageSize}`),
  getImage: (imageId: string) => request<ImageData>(`/images/${imageId}`),
  getDecision: (imageId: string) => request<DecisionData | null>(`/images/${imageId}/decision`),
  setDecision: (imageId: string, decision: 'pick' | 'reject') =>
    request<{ image_id: string; success: boolean }>(`/images/${imageId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),
  deleteDecision: (imageId: string) =>
    request<{ image_id: string; success: boolean }>(`/images/${imageId}/decision`, { method: 'DELETE' }),
  getPersons: () => request<PersonsData>('/persons'),
  renamePerson: (personId: string, name: string) =>
    request<{ person_id: string; name: string }>(`/persons/${personId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
    }),
  mergePerson: (personId: string, intoPersonId: string) =>
    request<{ reassigned_count: number; deleted_person_id: string }>(`/persons/${personId}/merge`, {
      method: 'POST',
      body: JSON.stringify({ into_person_id: intoPersonId }),
    }),
  deletePerson: (personId: string) =>
    request<{ deleted_person_id: string; deleted_face_count: number; unlinked_face_count: number }>(
      `/persons/${personId}`,
      { method: 'DELETE' },
    ),
  getFaces: (imageId: string) => request<FacesData>(`/images/${imageId}/faces`),
  getTrash: () => request<TrashData>('/trash'),
  restoreTrash: (imageId: string) =>
    request<{ image_id: string; success: boolean }>(`/trash/${imageId}/restore`, { method: 'POST' }),
}

export interface Gallery {
  gallery_id: string
  name: string
  path: string
  image_count: number
}

export interface GalleriesData {
  galleries: Gallery[]
}

export interface GalleryImage {
  image_id: string
  path: string
  thumbnail_path: string | null
  decision: 'pick' | 'reject' | null
}

export interface GalleryImagesData {
  images: GalleryImage[]
  total: number
  page: number
  page_size: number
}

export interface ImageData {
  image_id: string
  path: string
  metadata: Record<string, unknown>
  decision: 'pick' | 'reject' | null
  face_count: number
}

export interface DecisionData {
  image_id: string
  decision: 'pick' | 'reject'
  decided_at: string
}

export interface Person {
  person_id: string
  name: string
  created_at: string
  face_count: number
}

export interface PersonsData {
  persons: Person[]
}

export interface FaceBox {
  face_id: string
  image_id: string
  person_id: string | null
  bbox_x: number
  bbox_y: number
  bbox_w: number
  bbox_h: number
  detection_score: number
}

export interface FacesData {
  faces: FaceBox[]
}

export interface TrashItem {
  image_id: string
  original_path: string
  trashed_at: string
}

export interface TrashData {
  items: TrashItem[]
  count: number
}
