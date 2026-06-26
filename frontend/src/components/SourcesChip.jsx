/**
 * SourcesChip.jsx
 * Expandable chip that reveals retrieved textbook chunk excerpts.
 * This is the key UI element that proves the RAG pipeline is real.
 */
import { useState } from 'react'
import './SourcesChip.css'

export default function SourcesChip({ chunks = [] }) {
  const [open, setOpen] = useState(false)

  if (!chunks || chunks.length === 0) return null

  return (
    <div className="sources-chip-wrap">
      <button
        className={`sources-chip-btn ${open ? 'open' : ''}`}
        onClick={() => setOpen(v => !v)}
        aria-expanded={open}
      >
        <span className="sources-chip-icon">📖</span>
        <span>{chunks.length} source{chunks.length !== 1 ? 's' : ''}</span>
        <span className="sources-chip-arrow">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="sources-panel animate-fade-in">
          <div className="sources-panel-header">Retrieved from textbook</div>
          {chunks.map((chunk, i) => (
            <div key={chunk.id ?? i} className="source-item">
              <div className="source-meta">
                <span className="source-num">Chunk {i + 1}</span>
                <span className="source-sim">{Math.round(chunk.similarity * 100)}% match</span>
              </div>
              <p className="source-excerpt">{chunk.excerpt}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
