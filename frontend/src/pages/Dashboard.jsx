import { useState } from 'react'
import { Link } from 'react-router-dom'
import UploadPanel from '../components/UploadPanel'
import MetadataPanel from '../components/MetadataPanel'
import ScenePreviewMap from '../components/ScenePreviewMap'
import PipelineTracker from '../components/PipelineTracker'
import { enhancedGeotiffUrl } from '../services/api'

export default function Dashboard() {
  const [scene, setScene] = useState(null)
  const [runResult, setRunResult] = useState(null)
  const [activeLayer, setActiveLayer] = useState('original')

  function handleUploaded(uploadedScene) {
    setScene(uploadedScene)
    setRunResult(null)
    setActiveLayer('original')
  }

  function handleRunResult(result) {
    setRunResult(result)
    setActiveLayer('enhanced')
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-header-brand">
          <img src="/pixelnova-logo.png" alt="PIXELNOVA" className="header-logo" />
        </Link>
        <p className="tagline">From satellite data to a brighter tomorrow</p>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <UploadPanel onUploaded={handleUploaded} />
          <MetadataPanel scene={scene} />
          <PipelineTracker scene={scene} runResult={runResult} onRunResult={handleRunResult} />

          {runResult && (
            <a
              className="export-button"
              href={enhancedGeotiffUrl(scene.scene_id)}
              download
            >
              Export enhanced GeoTIFF
            </a>
          )}
        </aside>

        <main className="map-area">
          {runResult && (
            <div className="layer-toggle">
              <button
                className={activeLayer === 'original' ? 'active' : ''}
                onClick={() => setActiveLayer('original')}
              >
                Original
              </button>
              <button
                className={activeLayer === 'enhanced' ? 'active' : ''}
                onClick={() => setActiveLayer('enhanced')}
              >
                Enhanced
              </button>
              <button
                className={activeLayer === 'confidence' ? 'active' : ''}
                onClick={() => setActiveLayer('confidence')}
              >
                Confidence
              </button>
            </div>
          )}
          <ScenePreviewMap scene={scene} activeLayer={activeLayer} />
        </main>
      </div>
    </div>
  )
}
