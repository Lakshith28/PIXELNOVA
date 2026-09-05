export default function MetadataPanel({ scene }) {
  if (!scene) return null

  const { validation, accepted } = scene
  const { metadata, issues } = validation

  return (
    <div className="metadata-panel">
      <h3>
        Scene status:{' '}
        <span className={accepted ? 'status-ok' : 'status-fail'}>
          {accepted ? 'Accepted' : 'Rejected'}
        </span>
      </h3>

      {issues.length > 0 && (
        <ul className="issue-list">
          {issues.map((issue, i) => (
            <li key={i} className={`issue-${issue.level}`}>
              <strong>{issue.level.toUpperCase()}</strong> [{issue.code}]: {issue.message}
            </li>
          ))}
        </ul>
      )}

      {metadata && (
        <table className="metadata-table">
          <tbody>
            <tr><td>Dimensions</td><td>{metadata.width_px} × {metadata.height_px} px</td></tr>
            <tr><td>Bands</td><td>{metadata.band_count}</td></tr>
            <tr><td>Data type</td><td>{metadata.dtype}</td></tr>
            <tr><td>CRS</td><td>{metadata.crs || 'None'}</td></tr>
            <tr>
              <td>Pixel resolution</td>
              <td>
                {metadata.pixel_resolution?.x?.toFixed(2)} × {metadata.pixel_resolution?.y?.toFixed(2)}{' '}
                {metadata.pixel_resolution?.units}
              </td>
            </tr>
            <tr><td>Est. no-data %</td><td>{metadata.estimated_nodata_percent}%</td></tr>
          </tbody>
        </table>
      )}
    </div>
  )
}
