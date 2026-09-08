import { ImageOverlay, MapContainer, Rectangle, TileLayer, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import { confidencePreviewUrl, enhancedPreviewUrl, scenePreviewUrl } from '../services/api'

function FitToBounds({ bounds }) {
  const map = useMap()
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [20, 20] })
  }, [bounds, map])
  return null
}

export default function ScenePreviewMap({ scene, activeLayer = 'original' }) {
  if (!scene || !scene.accepted) {
    return (
      <div className="map-placeholder">
        <p>Upload a valid Sentinel-2 GeoTIFF to see its footprint here.</p>
      </div>
    )
  }

  const wgs84 = scene.validation.metadata.bounds_wgs84
  if (!wgs84) {
    return <div className="map-placeholder"><p>No footprint available (missing CRS).</p></div>
  }

  const bounds = [
    [wgs84.south, wgs84.west],
    [wgs84.north, wgs84.east],
  ]

  let overlayUrl = scenePreviewUrl(scene.scene_id)
  if (activeLayer === 'enhanced') overlayUrl = enhancedPreviewUrl(scene.scene_id)
  if (activeLayer === 'confidence') overlayUrl = confidencePreviewUrl(scene.scene_id)

  return (
    <MapContainer bounds={bounds} style={{ height: '100%', width: '100%' }} scrollWheelZoom>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
      <ImageOverlay key={overlayUrl} url={overlayUrl} bounds={bounds} opacity={0.9} />
      <Rectangle bounds={bounds} pathOptions={{ color: '#00e0a0', weight: 2, fillOpacity: 0 }} />
      <FitToBounds bounds={bounds} />
    </MapContainer>
  )
}
