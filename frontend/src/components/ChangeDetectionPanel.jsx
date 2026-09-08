import { useRef, useState } from 'react'
import { runChangeDetection, uploadScene } from '../services/api'
import './feature-change.css'

export default function ChangeDetectionPanel({ beforeScene, afterScene, onAfterUploaded, result, onResult }) {
  const inputRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  async function handleAfterFile(file) {
    if (!file) return
    setError(null); setUploading(true)
    try { const uploaded = await uploadScene(file); onAfterUploaded(uploaded); onResult(null) }
    catch (err) { setError(err.message) }
    finally { setUploading(false) }
  }

  async function handleCompare() {
    if (!beforeScene?.accepted || !afterScene?.accepted) return
    setError(null); setRunning(true)
    try { onResult(await runChangeDetection(beforeScene.scene_id, afterScene.scene_id)) }
    catch (err) { setError(err.message) }
    finally { setRunning(false) }
  }

  return (
    <div className="change-panel">
      <div className="change-scene-row">
        <div><span className="change-label">Before</span><span className="change-file">{beforeScene?.original_filename || 'Current scene'}</span></div>
        <div><span className="change-label">After</span><span className="change-file">{afterScene?.original_filename || 'Not uploaded'}</span></div>
      </div>
      <input ref={inputRef} type="file" accept=".tif,.tiff" style={{ display: 'none' }} onChange={(e) => handleAfterFile(e.target.files[0])} />
      <button type="button" className="secondary-action" disabled={!beforeScene?.accepted || uploading} onClick={() => inputRef.current?.click()}>{uploading ? 'Uploading after scene…' : afterScene ? 'Replace after scene' : 'Upload after-date GeoTIFF'}</button>
      <button type="button" className="compare-button" disabled={!beforeScene?.accepted || !afterScene?.accepted || running} onClick={handleCompare}>{running ? 'Comparing…' : 'Compare Changes'}</button>
      {error && <p className="run-message run-error">{error}</p>}
      {result && <div className="change-results">
        <div className="result-stat"><strong>{result.changed_percent}%</strong><span>area changed</span></div>
        <div className="transition-list">{result.transitions.length === 0 ? <p>No classified transitions detected.</p> : result.transitions.slice(0, 4).map((item) => <div className="transition-item" key={`${item.from_class}-${item.to_class}`}><span>{item.from_class}</span><b>→</b><span>{item.to_class}</span><em>{item.percent_of_changed}%</em></div>)}</div>
        <p className="run-message">{result.limitation}</p>
      </div>}
    </div>
  )
}
