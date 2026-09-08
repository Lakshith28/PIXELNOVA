import { useState } from 'react'
import { Link } from 'react-router-dom'
import UploadPanel from '../components/UploadPanel'
import MetadataPanel from '../components/MetadataPanel'
import ScenePreviewMap from '../components/ScenePreviewMap'
import PipelineTracker from '../components/PipelineTracker'
import { enhancedGeotiffUrl } from '../services/api'

export default function Dashboard() {
  const [scene, setScene] = useState(null)
  const [afterScene, setAfterScene] = useState(null)
  const [runResult, setRunResult] = useState(null)
  const [featureResult, setFeatureResult] = useState(null)
  const [changeResult, setChangeResult] = useState(null)
  const [activeLayer, setActiveLayer] = useState('original')

  function handleUploaded(uploadedScene) {
    setScene(uploadedScene)
    setAfterScene(null)
    setRunResult(null)
    setFeatureResult(null)
    setChangeResult(null)
    setActiveLayer('original')
  }

  function handleRunResult(result) { setRunResult(result); setActiveLayer('enhanced') }
  function handleFeatureResult(result) { setFeatureResult(result) }
  function handleChangeResult(result) { setChangeResult(result); if (result) setActiveLayer('change') }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-header-brand"><img src="/pixelnova-logo.png" alt="PIXELNOVA" className="header-logo" /></Link>
        <p className="tagline">From satellite data to a brighter tomorrow</p>
      </header>
      <div className="app-body">
        <aside className="sidebar">
          <UploadPanel onUploaded={handleUploaded} />
          <MetadataPanel scene={scene} />
          <PipelineTracker
            scene={scene}
            runResult={runResult}
            featureResult={featureResult}
            afterScene={afterScene}
            changeResult={changeResult}
            onRunResult={handleRunResult}
            onFeatureResult={handleFeatureResult}
            onAfterScene={setAfterScene}
            onChangeResult={handleChangeResult}
          />
          {runResult && <a className="export-button" href={enhancedGeotiffUrl(scene.scene_id)} download>Export enhanced GeoTIFF</a>}
        </aside>
        <main className="map-area">
          {(runResult || featureResult || changeResult) && (
            <div className="layer-toggle">
              <button className={activeLayer === 'original' ? 'active' : ''} onClick={() => setActiveLayer('original')}>Before</button>
              <button className={activeLayer === 'after' ? 'active' : ''} onClick={() => setActiveLayer('after')} disabled={!afterScene}>After</button>
              <button className={activeLayer === 'enhanced' ? 'active' : ''} onClick={() => setActiveLayer('enhanced')}>Enhanced</button>
              <button className={activeLayer === 'confidence' ? 'active' : ''} onClick={() => setActiveLayer('confidence')}>Confidence</button>
              <button className={activeLayer === 'features' ? 'active' : ''} onClick={() => setActiveLayer('features')} disabled={!featureResult}>Features</button>
              <button className={activeLayer === 'change' ? 'active' : ''} onClick={() => setActiveLayer('change')} disabled={!changeResult}>Changes</button>
            </div>
          )}
          <ScenePreviewMap scene={scene} activeLayer={activeLayer} afterScene={afterScene} />
        </main>
      </div>
    </div>
  )
}
