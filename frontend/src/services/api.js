// In production (Render static site build), set VITE_API_URL to the deployed
// backend's URL, e.g. https://pixelnova-backend.onrender.com/api
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export async function uploadScene(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/scenes/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `Upload failed with status ${res.status}`)
  }

  return res.json()
}

export function scenePreviewUrl(sceneId) {
  return `${API_BASE}/scenes/${sceneId}/preview`
}
