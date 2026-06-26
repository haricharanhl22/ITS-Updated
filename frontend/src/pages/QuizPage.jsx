import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useMastery } from '../hooks/useMastery'
import MasteryBar from '../components/MasteryBar'
import axios from 'axios'
import './QuizPage.css'

export default function QuizPage() {
  const { concept }   = useParams()
  const navigate      = useNavigate()
  const { token, user } = useAuth()
  const { getMasteryScore, refreshMastery } = useMastery()

  const decodedConcept = decodeURIComponent(concept || '')

  const [questions,  setQuestions]  = useState([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers,    setAnswers]    = useState({})
  const [revealed,   setRevealed]   = useState({})   // {qId → boolean}
  const [submitted,  setSubmitted]  = useState(false)
  const [result,     setResult]     = useState(null)
  const [loading,    setLoading]    = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error,      setError]      = useState(null)
  const [animationClass, setAnimationClass] = useState('')

  const masteryBefore = getMasteryScore(decodedConcept) / 100

  useEffect(() => {
    if (!decodedConcept || !token) return
    setLoading(true)
    axios.get(`/assessments/${encodeURIComponent(decodedConcept)}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => { setQuestions(r.data.questions); setLoading(false) })
      .catch(err => {
        setError(err?.response?.data?.detail || err.message || 'Failed to load quiz')
        setLoading(false)
      })
  }, [decodedConcept, token])

  const currentQ = questions[currentIdx]
  const totalQ   = questions.length
  const progressPct = totalQ > 0 ? ((currentIdx + 1) / totalQ) * 100 : 0
  const allAnswered  = totalQ > 0 && questions.every(q => answers[String(q.id)] !== undefined)

  const selectOption = (optIdx) => {
    if (submitted) return
    const qId = String(currentQ.id)
    if (answers[qId] !== undefined) return   // already answered — locked
    
    const isCorrect = optIdx === currentQ.correct_index
    setAnimationClass(isCorrect ? 'spring-bounce' : 'shake')
    
    setAnswers(prev => ({ ...prev, [qId]: optIdx }))
    setRevealed(prev => ({ ...prev, [qId]: true }))
    
    setTimeout(() => {
      setAnimationClass('')
    }, 800)
  }

  // Keyboard navigation for options (1, 2, 3, 4 keys)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!currentQ || submitted || loading) return
      const qId = String(currentQ.id)
      if (revealed[qId]) return // already revealed
      if (['1', '2', '3', '4'].includes(e.key)) {
        const optIdx = parseInt(e.key, 10) - 1
        if (optIdx < currentQ.options.length) {
          selectOption(optIdx)
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentQ, revealed, submitted, loading])

  const handleSubmit = async () => {
    if (!allAnswered || submitting) return
    setSubmitting(true)
    setError(null)
    try {
      const { data } = await axios.post('/assessments/submit', {
        concept:    decodedConcept,
        answers,
      }, { headers: { Authorization: `Bearer ${token}` } })
      setResult(data)
      setSubmitted(true)
      refreshMastery()
    } catch (err) {
      setError(err?.response?.data?.detail || err.message)
    } finally {
      setSubmitting(false)
    }
  }

  /* ── Loading ── */
  if (loading) return (
    <div className="quiz-page">
      <div className="quiz-loading">
        <div className="quiz-loading-skeleton" />
        <div className="quiz-loading-skeleton" style={{ width: '70%' }} />
        <div className="quiz-loading-skeleton" style={{ width: '90%', height: 80 }} />
      </div>
    </div>
  )

  /* ── Error ── */
  if (error && !submitted) return (
    <div className="quiz-page">
      <div className="quiz-error">
        <div style={{ fontSize: 40 }}>⚠️</div>
        <strong>{error}</strong>
        <button className="btn btn-outline btn-sm" onClick={() => navigate('/chat')}>← Back to Chat</button>
      </div>
    </div>
  )

  /* ── Result screen ── */
  if (submitted && result) {
    const scorePct   = Math.round(result.score * 100)
    const newMastery = Math.round(result.new_mastery * 100)
    const deltaPct   = Math.round(result.mastery_delta * 100)
    const isUp       = deltaPct >= 0
    const emoji      = scorePct >= 80 ? '🏆' : scorePct >= 60 ? '✅' : scorePct >= 40 ? '📚' : '💪'
    const xpGained   = Math.round(result.score * 100)

    return (
      <div className="quiz-page animate-fade-in">
        <div className="quiz-result animate-slide-up">
          {/* Score ring */}
          <div className="quiz-score-ring" style={{ '--score': scorePct }}>
            <svg viewBox="0 0 120 120" width="160" height="160">
              <circle cx="60" cy="60" r="52" fill="none" stroke="var(--bg-surface-2)" strokeWidth="10" />
              <circle
                cx="60" cy="60" r="52" fill="none"
                stroke={scorePct >= 80 ? 'var(--green)' : scorePct >= 50 ? 'var(--cyan)' : 'var(--orange)'}
                strokeWidth="10" strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 52}`}
                strokeDashoffset={`${2 * Math.PI * 52 * (1 - scorePct / 100)}`}
                transform="rotate(-90 60 60)"
                style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.34,1.56,0.64,1)', filter: `drop-shadow(0 0 8px ${scorePct >= 80 ? 'var(--green)' : 'var(--cyan)'})` }}
              />
            </svg>
            <div className="quiz-score-inner">
              <span className="quiz-score-num">{scorePct}%</span>
              <span className="quiz-score-label">SCORE</span>
            </div>
          </div>

          <h1 className="quiz-result-title">
            {emoji} {scorePct >= 80 ? 'Excellent work!' : scorePct >= 60 ? 'Good job!' : scorePct >= 40 ? 'Keep practising!' : "Don't give up!"}
          </h1>

          <div className="quiz-result-card">
            {[
              { k: 'Concept',          v: decodedConcept },
              { k: 'Correct answers',  v: `${result.correct_count} / ${result.total}` },
              { k: 'XP Earned',        v: `+${xpGained} XP` },
            ].map(({ k, v }) => (
              <div key={k} className="quiz-result-row">
                <span className="quiz-result-key">{k}</span>
                <span className="quiz-result-val" style={{ color: k === 'XP Earned' ? 'var(--green)' : 'inherit', fontWeight: 'bold' }}>{v}</span>
              </div>
            ))}
            <div className="quiz-result-row">
              <span className="quiz-result-key">Mastery update</span>
              <div className="quiz-mastery-transition">
                <span className="quiz-mastery-from">{Math.round(masteryBefore * 100)}%</span>
                <span className="quiz-mastery-arrow">→</span>
                <span className="quiz-mastery-to" style={{ color: isUp ? 'var(--green)' : 'var(--orange)' }}>
                  {newMastery}%
                </span>
                <span className={`quiz-mastery-delta ${isUp ? 'positive' : 'negative'}`}>
                  {isUp ? '+' : ''}{deltaPct}%
                </span>
              </div>
            </div>
            <div className="quiz-result-row">
              <span className="quiz-result-key">Progress bar</span>
              <span style={{ flex: 1 }}><MasteryBar score={result.new_mastery} showPct /></span>
            </div>
          </div>

          <div className="quiz-result-actions">
            <button id="btn-back-to-chat" className="btn btn-primary" onClick={() => navigate('/chat')}>← Back to Chat</button>
            <button id="btn-retake-quiz"  className="btn btn-outline" onClick={() => {
              setAnswers({}); setRevealed({}); setCurrentIdx(0); setSubmitted(false); setResult(null)
            }}>Retake Quiz</button>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>Dashboard</button>
          </div>
        </div>
      </div>
    )
  }

  /* ── Quiz questions ── */
  const qId  = currentQ ? String(currentQ.id) : null
  const ans  = qId ? answers[qId] : undefined
  const isRevealed = qId ? !!revealed[qId] : false

  return (
    <div className="quiz-page">
      <div className="quiz-header animate-fade-in">
        <button id="btn-quiz-back" className="quiz-back-btn" onClick={() => navigate('/chat')}>← Back</button>
        <div className="quiz-title">
          <h1>{decodedConcept} Quiz</h1>
          <p>Test your Python knowledge</p>
        </div>
      </div>

      {/* Progress */}
      <div className="quiz-progress-wrap">
        <div className="quiz-progress-label">
          <span>Question {currentIdx + 1} of {totalQ}</span>
          <span>{Object.keys(answers).length} answered</span>
        </div>
        <div className="quiz-progress-track">
          <div className="quiz-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      {/* Question card */}
      {currentQ && (
        <div className="quiz-question-card animate-fade-in">
          <div className="quiz-q-number">Question {currentIdx + 1}</div>
          <div className="quiz-q-text">{currentQ.text}</div>

          <div className="quiz-options">
            {currentQ.options.map((optText, i) => {
              const isSelected = ans === i
              const isCorrect  = i === currentQ.correct_index
              let status = ''
              if (isRevealed) {
                status = isCorrect ? 'correct' : (isSelected ? 'wrong' : '')
              }
              return (
                <button
                  key={i}
                  className={`quiz-option ${isSelected ? 'selected' : ''} ${status} ${isSelected ? animationClass : ''}`}
                  onClick={() => selectOption(i)}
                  disabled={isRevealed}
                  aria-pressed={isSelected}
                >
                  <span className="quiz-option-letter">{String.fromCharCode(65 + i)}</span>
                  <span className="quiz-option-text">{optText}</span>
                  {isRevealed && isCorrect && <span className="quiz-option-icon">✓</span>}
                  {isRevealed && isSelected && !isCorrect && <span className="quiz-option-icon">✗</span>}
                </button>
              )
            })}
          </div>

          {isRevealed && (
            <>
              <div className={`quiz-feedback animate-fade-in ${ans === currentQ.correct_index ? 'feedback-correct' : 'feedback-wrong'}`}>
                {ans === currentQ.correct_index ? '✅ Correct!' : `❌ Incorrect — the correct answer is ${String.fromCharCode(65 + currentQ.correct_index)}`}
              </div>
              <div className="quiz-explanation-card animate-fade-in" style={{ padding: '12px 16px', background: 'var(--bg-surface-2)', border: '1px solid var(--border)', borderRadius: '12px', fontSize: '0.82rem', lineHeight: '1.5', color: 'var(--text-subtle)' }}>
                <strong>Constructive explanation:</strong> Option {String.fromCharCode(65 + currentQ.correct_index)} is the correct syntax for Python {decodedConcept}. In Python, <code>{currentQ.options[currentQ.correct_index]}</code> represents the standard, idiomatic approach to solve this problem, aligning with pep8 and best practices.
              </div>
            </>
          )}

          <div className="quiz-nav">
            <button id="btn-quiz-prev" className="btn btn-ghost btn-sm"
              onClick={() => setCurrentIdx(i => Math.max(0, i - 1))}
              disabled={currentIdx === 0}>← Prev</button>

            {currentIdx < totalQ - 1 ? (
              <button id="btn-quiz-next" className="btn btn-primary btn-sm"
                onClick={() => setCurrentIdx(i => Math.min(totalQ - 1, i + 1))}>
                Next →
              </button>
            ) : (
              <button id="btn-quiz-submit" className="btn btn-primary"
                onClick={handleSubmit}
                disabled={!allAnswered || submitting}>
                {submitting ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Submitting…</> : 'Submit Quiz'}
              </button>
            )}
          </div>
          {error && <div className="alert-error animate-fade-in" style={{ marginTop: 12 }}>⚠ {error}</div>}
        </div>
      )}
    </div>
  )
}
