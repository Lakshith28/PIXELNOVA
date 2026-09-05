import { useState } from 'react'
import UploadPanel from './components/UploadPanel'
import MetadataPanel from './components/MetadataPanel'
import ScenePreviewMap from './components/ScenePreviewMap'

export default function App() {
  const [scene, setScene] = useState(null)

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>PIXELNOVEL</h1>
        <p className="tagline">From Pixels to Decisions — Phase 1 Skeleton</p>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <UploadPanel onUploaded={setScene} />
          <MetadataPanel scene={scene} />
        </aside>

        <main className="map-area">
          <ScenePreviewMap scene={scene} />
        </main>
      </div>
    </div>
  )
}
