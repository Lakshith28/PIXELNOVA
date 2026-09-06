const STAGES = [
  {
    id: 'input',
    label: '01 Input',
    doneWhen: (scene) => Boolean(scene?.accepted),
    items: (scene) => [
      { label: 'GeoTIFF validated', done: Boolean(scene?.accepted) },
      { label: 'Georeferenced', done: Boolean(scene?.validation?.metadata?.crs) },
      {
        label: `${scene?.validation?.metadata?.pixel_resolution?.x?.toFixed(0) ?? '—'} m resolution`,
        done: Boolean(scene?.accepted),
      },
      { label: `${scene?.validation?.metadata?.band_count ?? '—'} bands available`, done: Boolean(scene?.accepted) },
    ],
  },
  {
    id: 'preprocessing',
    label: '02 Preprocessing',
    status: 'Not yet built',
  },
  {
    id: 'super-resolution',
    label: '03 Super-Resolution',
    status: 'Not yet built',
  },
  {
    id: 'confidence',
    label: '04 Confidence',
    status: 'Not yet built',
  },
  {
    id: 'features',
    label: '05 Features',
    status: 'Not yet built',
  },
  {
    id: 'change',
    label: '06 Change Detection',
    status: 'Not yet built',
  },
]

export default function PipelineTracker({ scene, onRunClicked, runMessage }) {
  const canRun = Boolean(scene?.accepted)

  return (
    <div className="pipeline-tracker">
      {STAGES.map((stage) => {
        const isInputStage = stage.id === 'input'
        const isDone = isInputStage && stage.doneWhen(scene)

        return (
          <div
            key={stage.id}
            className={`stage ${isInputStage ? (isDone ? 'stage-done' : 'stage-waiting') : 'stage-pending'}`}
          >
            <div className="stage-header">
              <span className="stage-label">{stage.label}</span>
              {!isInputStage && <span className="stage-badge">{stage.status}</span>}
            </div>
            {isInputStage && scene && (
              <ul className="stage-checklist">
                {stage.items(scene).map((item) => (
                  <li key={item.label} className={item.done ? 'check-done' : 'check-pending'}>
                    {item.done ? '✓' : '·'} {item.label}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )
      })}

      <button
        type="button"
        className="run-ai-button"
        disabled={!canRun}
        onClick={onRunClicked}
        title={canRun ? undefined : 'Upload a valid scene first'}
      >
        Run PIXELNOVEL AI
      </button>
      {runMessage && <p className="run-message">{runMessage}</p>}
    </div>
  )
}
