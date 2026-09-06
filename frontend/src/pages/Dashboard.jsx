import { useState } from 'react'
import { Link } from 'react-router-dom'
import UploadPanel from '../components/UploadPanel'
import MetadataPanel from '../components/MetadataPanel'
import ScenePreviewMap from '../components/ScenePreviewMap'
import PipelineTracker from '../components/PipelineTracker'

export default function Dashboard() {
  const [scene, setScene] = useState(null)
  const [runMessage, setRunMessage] = useState(null)

  function handleRunClicked() {
    setRunMessage(
      'The AI reconstruction pipeline (stages 02–06) isn\u2019t built yet \u2014 this is a UI preview of the intended workflow. Stage 01 above is fully real.'
    )
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-header-brand">PIXELNOVEL</Link>
        <p className="tagline">From Pixels to Decisions — Phase 1 Skeleton</p>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <UploadPanel onUploaded={(s) => { setScene(s); setRunMessage(null) }} />
          <MetadataPanel scene={scene} />
          <PipelineTracker scene={scene} onRunClicked={handleRunClicked} runMessage={runMessage} />
        </aside>

        <main className="map-area">
          <ScenePreviewMap scene={scene} />
        </main>
      </div>
    </div>
  )
}
