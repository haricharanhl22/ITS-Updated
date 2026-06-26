import { useState, useRef, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import axios from 'axios'
import './PDFUploader.css'

/**
 * PDFUploader — drag-and-drop PDF ingestion into the RAG knowledge base.
 *
 * Flow:
 *   1. User drags/drops or clicks to select a PDF
 *   2. File is validated (type, size ≤ 50 MB)
 *   3. POST /api/admin/ingest-pdf (multipart/form-data)
 *   4. Progress states: idle → uploading → processing → done / error
 *   5. On success: shows page count, chunk count, total KB size
 */
export default function PDFUploader({ onIngested }) {
  const { token } = useAuth()
  const fileRef = useRef(null)

  const [file,      setFile]      = useState(null)
  const [stage,     setStage]     = useState('idle')  // idle | uploading | processing | done | error
  const [progress,  setProgress]  = useState(0)
  const [result,    setResult]    = useState(null)
  const [error,     setError]     = useState(null)
  const [dragging,  setDragging]  = useState(false)

  const MAX_SIZE_MB = 50

  const resetState = () => {
    setFile(null)
    setStage('idle')
    setProgress(0)
    setResult(null)
    setError(null)
  }

  const validateFile = (f) => {
    if (!f) return 'No file selected.'
    if (!f.name.toLowerCase().endsWith('.pdf'))
      return 'Only PDF files are accepted. Please upload a .pdf file.'
    if (f.size > MAX_SIZE_MB * 1024 * 1024)
      return `File is too large. Maximum size is ${MAX_SIZE_MB} MB.`
    return null
  }

  const handleFile = (f) => {
    const err = validateFile(f)
    if (err) { setError(err); return }
    setFile(f)
    setError(null)
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    handleFile(dropped)
  }, [])

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const handleDragLeave = () => setDragging(false)

  const handleInputChange = (e) => {
    handleFile(e.target.files[0])
    e.target.value = ''
  }

  const handleUpload = async () => {
    if (!file || stage !== 'idle') return

    const err = validateFile(file)
    if (err) { setError(err); return }

    const formData = new FormData()
    formData.append('file', file)

    setStage('uploading')
    setProgress(10)
    setError(null)

    try {
      setProgress(30)
      setStage('processing')

      const { data } = await axios.post('/api/admin/ingest-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        onUploadProgress: (e) => {
          const pct = Math.round((e.loaded / e.total) * 60) + 20
          setProgress(Math.min(pct, 80))
        },
      })

      setProgress(100)
      setResult(data)
      setStage('done')
      if (onIngested) onIngested(data)
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : err.message || 'Upload failed.')
      setStage('error')
    }
  }

  const fileSizeLabel = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  return (
    <div className="uploader-root">
      <div className="uploader-header">
        <span className="uploader-icon">📚</span>
        <div>
          <div className="uploader-title">Upload Textbook PDF</div>
          <div className="uploader-subtitle">Ingest Python content into the RAG knowledge base</div>
        </div>
      </div>

      {/* Drop zone */}
      {stage === 'idle' || stage === 'error' ? (
        <div
          className={`uploader-dropzone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !file && fileRef.current?.click()}
          role="button"
          aria-label="Drop PDF here or click to select"
          id="pdf-dropzone"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            onChange={handleInputChange}
            style={{ display: 'none' }}
            id="pdf-file-input"
          />

          {file ? (
            <div className="uploader-file-selected animate-fade-in">
              <span className="uploader-file-icon">📄</span>
              <div className="uploader-file-info">
                <div className="uploader-file-name">{file.name}</div>
                <div className="uploader-file-size">{fileSizeLabel(file.size)}</div>
              </div>
              <button
                className="uploader-remove-btn"
                onClick={(e) => { e.stopPropagation(); resetState() }}
                aria-label="Remove file"
                id="btn-remove-pdf"
              >
                ✕
              </button>
            </div>
          ) : (
            <div className="uploader-placeholder animate-fade-in">
              <div className="uploader-drop-icon">{dragging ? '📥' : '⬆️'}</div>
              <div className="uploader-drop-text">
                {dragging ? 'Release to upload' : 'Drag & drop a PDF here'}
              </div>
              <div className="uploader-drop-sub">or click to browse — max {MAX_SIZE_MB} MB</div>
            </div>
          )}
        </div>
      ) : null}

      {/* Error message */}
      {error && (
        <div className="uploader-error animate-fade-in" role="alert">
          <span>⚠️</span> {error}
        </div>
      )}

      {/* Progress bar (uploading / processing) */}
      {(stage === 'uploading' || stage === 'processing') && (
        <div className="uploader-progress-wrap animate-fade-in">
          <div className="uploader-progress-label">
            <span className="uploader-spinner" />
            <span>
              {stage === 'uploading'
                ? `Uploading ${file?.name}…`
                : '🔬 Extracting text, generating embeddings…'}
            </span>
          </div>
          <div className="uploader-progress-track">
            <div
              className="uploader-progress-fill"
              style={{ width: `${progress}%`, transition: 'width 0.4s ease' }}
            />
          </div>
          <div className="uploader-progress-pct">{progress}%</div>
        </div>
      )}

      {/* Success result */}
      {stage === 'done' && result && (
        <div className="uploader-result animate-slide-up">
          <div className="uploader-result-icon">✅</div>
          <div className="uploader-result-body">
            <div className="uploader-result-title">Ingestion Complete!</div>
            <div className="uploader-result-message">{result.message}</div>
            <div className="uploader-result-stats">
              <div className="uploader-stat">
                <span className="uploader-stat-val">{result.pages_found}</span>
                <span className="uploader-stat-label">Pages</span>
              </div>
              <div className="uploader-stat">
                <span className="uploader-stat-val">{result.chunks_built}</span>
                <span className="uploader-stat-label">Chunks built</span>
              </div>
              <div className="uploader-stat">
                <span className="uploader-stat-val">{result.total_chunks}</span>
                <span className="uploader-stat-label">Total in DB</span>
              </div>
            </div>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={resetState}
            id="btn-upload-another"
          >
            Upload another
          </button>
        </div>
      )}

      {/* Upload button */}
      {file && (stage === 'idle' || stage === 'error') && (
        <button
          className="btn btn-primary btn-full uploader-submit animate-fade-in"
          onClick={handleUpload}
          disabled={!file}
          id="btn-ingest-pdf"
        >
          🚀 Ingest PDF into Knowledge Base
        </button>
      )}
    </div>
  )
}
