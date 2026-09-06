import { useState } from 'react'
import { runAiPipeline } from '../services/api'

const INPUT_ITEMS = (scene) => [
  { label: 'GeoTIFF validated', done: Boolean(scene?.accepted) },
  { label: 'Georeferenced', done: Boolean(scene?.validation?.metadata?.crs) },
  {
    label: `${scene?.validation?.metadata?.pixel_resolution?.x?.toFixed(0) ?? '—'} m resolution`,
    done: Boolean(scene?.accepted),
  },
  { label: `${scene?.validation?.metadata?.band_count ?? '—'} bands available`, done: Boolean(scene?.accepted) },
]

export default function PipelineTracker({ scene, runResult, onRunResult }) {
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  const canRun = Boolean(scene?.accepted) && !running

  async function handleRun() {
    setError(null)
    setRunning(true)
    try {
      const result = await runAiPipeline(scene.scene_id)
      onRunResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  const stage2Done = Boolean(runResult)
  const stage3Done = Boolean(runResult)
  const stage4Done = Boolean(runResult)

  return (
    <div className="pipeline-tracker">
      <div className={`stage ${scene?.accepted ? 'stage-done' : 'stage-waiting'}`}>
        <div className="stage-header">
          <span className="stage-label">01 Input</span>
        </div>
        {scene && (
          <ul className="stage-checklist">
            {INPUT_ITEMS(scene).map((item) => (
              <li key={item.label} className={item.done ? 'check-done' : 'check-pending'}>
                {item.done ? '✓' : '·'} {item.label}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={`stage ${stage2Done ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header">
          <span className="stage-label">02 Preprocessing</span>
          <span className="stage-badge">{stage2Done ? 'Done' : 'Waiting'}</span>
        </div>
        {stage2Done && (
          <ul className="stage-checklist">
            <li className="check-done">✓ Reflectance normalized</li>
            <li className="check-done">✓ Input resolution: {runResult.input_resolution_m} m</li>
          </ul>
        )}
      </div>

      <div className={`stage ${stage3Done ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header">
          <span className="stage-label">03 Super-Resolution</span>
          <span className="stage-badge">{stage3Done ? 'Classical baseline' : 'Waiting'}</span>
        </div>
        {stage3Done && (
          <ul className="stage-checklist">
            <li className="check-done">
              ✓ {runResult.input_resolution_m} m → {runResult.output_resolution_m} m ({runResult.scale_factor}×)
            </li>
            <li className="check-pending">· Not a trained AI model yet — classical upsampling only</li>
          </ul>
        )}
      </div>

      <div className={`stage ${stage4Done ? 'stage-done' : 'stage-pending'}`}>
        <div className="stage-header">
          <span className="stage-label">04 Confidence</span>
          <span className="stage-badge">{stage4Done ? 'Heuristic' : 'Waiting'}</span>
        </div>
        {stage4Done && (
          <ul className="stage-checklist">
            <li className="check-done">✓ High: {runResult.high_confidence_pct}%</li>
            <li className="check-done">✓ Medium: {runResult.medium_confidence_pct}%</li>
            <li className="check-done">✓ Low: {runResult.low_confidence_pct}%</li>
          </ul>
        )}
      </div>

      <div className="stage stage-pending">
        <div className="stage-header">
          <span className="stage-label">05 Features</span>
          <span className="stage-badge">Not yet built</span>
        </div>
      </div>

      <div className="stage stage-pending">
        <div className="stage-header">
          <span className="stage-label">06 Change Detection</span>
          <span className="stage-badge">Not yet built</span>
        </div>
      </div>

      <button
        type="button"
        className="run-ai-button"
        disabled={!canRun}
        onClick={handleRun}
        title={canRun ? undefined : 'Upload a valid scene first'}
      >
        {running ? 'Processing…' : 'Run PIXELNOVA AI'}
      </button>

      {error && <p className="run-message run-error">{error}</p>}

      {runResult && (
        <p className="run-message">{runResult.disclaimer}</p>
      )}
    </div>
  )
}
