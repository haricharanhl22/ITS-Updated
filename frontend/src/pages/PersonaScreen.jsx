import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePersona, CONCEPTS } from '../context/PersonaContext'
import RadialProgress from '../components/RadialProgress'
import axios from 'axios'
import './PersonaScreen.css'

const PERSONA_DEFS = [
  {
    level: 'beginner',
    displayName: 'Ava',
    emoji: '🌱',
    tagline: 'Just getting started',
    description: 'New to Python. Learning the basics of variables, data types, and simple programs.',
    color: '#F97316',
    glow: 'rgba(249,115,22,0.25)',
    masteryHint: [0.28, 0.12, 0.18],
  },
  {
    level: 'intermediate',
    displayName: 'Marcus',
    emoji: '📚',
    tagline: 'Building solid skills',
    description: 'Comfortable with the basics. Exploring functions, loops, and OOP fundamentals.',
    color: '#06B6D4',
    glow: 'rgba(6,182,212,0.25)',
    masteryHint: [0.72, 0.58, 0.65],
  },
  {
    level: 'advanced',
    displayName: 'Priya',
    emoji: '🔥',
    tagline: 'Pushing the limits',
    description: 'Strong foundation. Mastering complex OOP, error handling, and Pythonic patterns.',
    color: '#A855F7',
    glow: 'rgba(168,85,247,0.25)',
    masteryHint: [0.95, 0.90, 0.92],
  },
]

const PREVIEW_CONCEPTS = ['Variables', 'Functions', 'Loops']

export default function PersonaScreen() {
  const { selectPersona, isSelected } = usePersona()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(null)  // which persona is loading
  const [error, setError]     = useState('')
  const [hovered, setHovered] = useState(null)

  useEffect(() => {
    if (isSelected) navigate('/dashboard', { replace: true })
  }, [isSelected, navigate])

  const handleSelect = async (level) => {
    setError('')
    setLoading(level)
    try {
      await selectPersona(level)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Failed to load persona. Is the backend running?'
      setError(msg)
      setLoading(null)
    }
  }

  return (
    <div className="persona-screen">
      {/* Background orbs */}
      <div className="persona-orb persona-orb-1" />
      <div className="persona-orb persona-orb-2" />
      <div className="persona-orb persona-orb-3" />

      <div className="persona-content">
        {/* Header */}
        <div className="persona-header animate-fade-in-up">
          <div className="persona-logo">
            <span className="persona-logo-icon">🎓</span>
          </div>
          <h1 className="persona-title">
            Welcome to <span className="gradient-text">HCAI-ITS</span>
          </h1>
          <p className="persona-subtitle">
            Your intelligent Python tutor. Choose a demo profile to begin.
          </p>
        </div>

        {/* Cards */}
        <div className="persona-cards">
          {PERSONA_DEFS.map((p, idx) => (
            <button
              key={p.level}
              id={`persona-${p.level}`}
              className={`persona-card animate-fade-in-up ${hovered === p.level ? 'hovered' : ''}`}
              style={{
                '--card-color': p.color,
                '--card-glow': p.glow,
                animationDelay: `${idx * 0.1 + 0.15}s`,
              }}
              onClick={() => handleSelect(p.level)}
              onMouseEnter={() => setHovered(p.level)}
              onMouseLeave={() => setHovered(null)}
              disabled={!!loading}
            >
              {/* Glow border */}
              <div className="persona-card-glow" />

              {/* Avatar */}
              <div className="persona-avatar" style={{ background: `radial-gradient(circle at 40% 40%, ${p.color}44, transparent)`, border: `2px solid ${p.color}55` }}>
                <span className="persona-avatar-emoji">{p.emoji}</span>
              </div>

              {/* Info */}
              <div className="persona-info">
                <div className="persona-name">{p.displayName}</div>
                <div className="persona-tagline" style={{ color: p.color }}>{p.tagline}</div>
                <p className="persona-desc">{p.description}</p>
              </div>

              {/* Mini mastery preview */}
              <div className="persona-mastery-preview">
                {PREVIEW_CONCEPTS.map((c, ci) => (
                  <div key={c} className="persona-mastery-item">
                    <RadialProgress
                      score={p.masteryHint[ci]}
                      size={52}
                      stroke={4}
                      showPct
                      animate={hovered === p.level}
                    />
                    <span className="persona-mastery-concept">{c}</span>
                  </div>
                ))}
              </div>

              {/* CTA */}
              <div className="persona-cta" style={{ background: `linear-gradient(135deg, ${p.color}dd, ${p.color}88)` }}>
                {loading === p.level ? (
                  <><span className="spinner" style={{ width: 14, height: 14 }} /> Loading…</>
                ) : (
                  `Continue as ${p.displayName} →`
                )}
              </div>
            </button>
          ))}
        </div>

        {error && (
          <div className="persona-error alert-error animate-fade-in">
            ⚠️ {error}
          </div>
        )}

        <p className="persona-footer">
          No account needed · Demo data · Switch personas anytime
        </p>
      </div>
    </div>
  )
}
