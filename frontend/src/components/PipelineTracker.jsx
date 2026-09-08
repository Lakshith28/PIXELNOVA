import { useState } from 'react'
import { runAiPipeline, runFeatureExtraction } from '../services/api'
import ChangeDetectionPanel from './ChangeDetectionPanel'

const INPUT_ITEMS = (scene) => [
  { label: 'GeoTIFF validated', done: Boolean(scene?.accepted) },
  { label: 'Georeferenced', done: Boolean(scene?.validation?.metadata?.crs) },
  { label: `${scene?.validation?.metadata?.pixel_resolution?.x?.toFixed(0) ?? '—'} m resolution`, done: Boolean(scene?.accepted) },
  { label: `${scene?.validation?.metadata?.band_count ?? '—'} bands available`, done: Boolean(scene?.accepted) },
]

export default function PipelineTracker({ scene, runResult, featureResult, afterScene, changeResult, onRunResult, onFeatureResult, onAfterScene, onChangeResult }) {
  const [running, setRunning] = useState(false)
  const [featureRunning, setFeatureRunning] = useState(false)
  const [error, setError] = useState(null)
  const canRun = Boolean(scene?.accepted) && !running

  async function handleRun() {
    setError(null); setRunning(true)
    try {
      const result = await runAiPipeline(scene.scene_id)
      onRunResult(result)
      setFeatureRunning(true)
      try { onFeatureResult(await runFeatureExtraction(scene.scene_id)) }
      finally { setFeatureRunning(false) }
    } catch (err) { setError(err.message) }
    finally { setRunning(false) }
  }

  const stageDone = Boolean(runResult)
  const stage5Done = Boolean(featureResult)
  const stage6Done = Boolean(changeResult)

  return (
    <div className="pipeline-tracker">
      <div className={`stage ${scene?.accepted ? 'stage-done' : 'stage-waiting'}`}>
        <div className="stage-header"><span className="stage-label">01 Input</span></div>
        {scene && <ul className="stage-checklist">{INPUT_ITEMS(scene).map((item) => <li key={item.label} className={item.done ? 'check-done' : 'check-pending'}>{item.done ? '✓' : '·'} {item.label}</li>)}</ul>}
      </div>

      <div className={`stage ${stageDone ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header"><span className="stage-label">02 Preprocessing</span><span className="stage-badge">{stageDone ? 'Done' : 'Waiting'}</span></div>
        {stageDone && <ul className="stage-checklist"><li className="check-done">✓ Reflectance normalized</li><li className="check-done">✓ Input resolution: {runResult.input_resolution_m} m</li></ul>}
      </div>

      <div className={`stage ${stageDone ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header"><span className="stage-label">03 Super-Resolution</span><span className="stage-badge">{stageDone ? (runResult.method_label === 'trained_cnn_espcn_onnx' ? 'Trained CNN' : 'Classical baseline') : 'Waiting'}</span></div>
        {stageDone && <ul className="stage-checklist"><li className="check-done">✓ {runResult.input_resolution_m} m → {runResult.output_resolution_m} m ({runResult.scale_factor}×)</li><li className={runResult.method_label === 'trained_cnn_espcn_onnx' ? 'check-done' : 'check-pending'}>{runResult.method_label === 'trained_cnn_espcn_onnx' ? '✓ Small trained CNN (ESPCN), not a research-grade model' : '· Trained model unavailable — used classical upsampling'}</li></ul>}
      </div>

      <div className={`stage ${stageDone ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header"><span className="stage-label">04 Confidence</span><span className="stage-badge">{stageDone ? 'Heuristic' : 'Waiting'}</span></div>
        {stageDone && <ul className="stage-checklist"><li className="check-done">✓ High: {runResult.high_confidence_pct}%</li><li className="check-done">✓ Medium: {runResult.medium_confidence_pct}%</li><li className="check-done">✓ Low: {runResult.low_confidence_pct}%</li></ul>}
      </div>

      <div className={`stage ${stage5Done ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header"><span className="stage-label">05 Features</span><span className="stage-badge">{stage5Done ? 'Ready' : featureRunning ? 'Analyzing…' : 'Waiting'}</span></div>
        {stage5Done && <ul className="stage-checklist"><li className="check-done">✓ Vegetation: {featureResult.stats['Vegetation']?.percent ?? 0}%</li><li className="check-done">✓ Water: {featureResult.stats['Water']?.percent ?? 0}%</li><li className="check-done">✓ Built-up / bare: {featureResult.stats['Built-up / bare']?.percent ?? 0}%</li></ul>}
      </div>

      <div className={`stage ${stage6Done ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header"><span className="stage-label">06 Change Detection</span><span className="stage-badge">{stage6Done ? 'Complete' : 'Compare two dates'}</span></div>
        {scene && <ChangeDetectionPanel beforeScene={scene} afterScene={afterScene} onAfterUploaded={onAfterScene} result={changeResult} onResult={onChangeResult} />}
      </div>

      <button type="button" className="run-ai-button" disabled={!canRun} onClick={handleRun}>{running ? 'Processing…' : 'Run PIXELNOVA AI'}</button>
      {error && <p className="run-message run-error">{error}</p>}
      {runResult && <p className="run-message">{runResult.disclaimer}</p>}
    </div>
  )
}
