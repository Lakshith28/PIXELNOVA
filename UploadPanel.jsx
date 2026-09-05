import { useRef, useState } from 'react'
import { uploadScene } from '../services/api'

export default function UploadPanel({ onUploaded }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  async function handleFile(file) {
    if (!file) return
    setError(null)
    setIsUploading(true)
    try {
      const result = await uploadScene(file)
      onUploaded(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div
      className={`upload-panel ${isDragging ? 'dragging' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragging(false)
        handleFile(e.dataTransfer.files[0])
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".tif,.tiff"
        style={{ display: 'none' }}
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {isUploading ? (
        <p>Uploading &amp; validating scene…</p>
      ) : (
        <>
          <p className="upload-title">Drop a Sentinel-2 GeoTIFF here</p>
          <p className="upload-subtitle">or click to browse (.tif / .tiff)</p>
        </>
      )}
      {error && <p className="upload-error">{error}</p>}
    </div>
  )
}
