import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useMastery, CONCEPTS } from '../hooks/useMastery'
import RadialProgress from '../components/RadialProgress'
import Sparkline from '../components/Sparkline'
import axios from 'axios'
import './DashboardPage.css'

const CONCEPT_EMOJI = {
  'Variables': '📦', 'Functions': '⚙️', 'Loops': '🔁',
  'OOP': '🏗️', 'Strings': '🔤', 'Lists': '📋',
  'Dictionaries': '📖', 'Error Handling': '⚠️',
}

const TIERS = [
  {
    id: 1,
    name: 'Tier 1: Foundations',
    concepts: ['Variables', 'Strings', 'Lists'],
    description: 'Learn the basic syntax and standard structures in Python.'
  },
  {
    id: 2,
    name: 'Tier 2: Control Flow & Structure',
    concepts: ['Loops', 'Functions', 'Dictionaries'],
    description: 'Structure logic and build reusable operations.'
  },
  {
    id: 3,
    name: 'Tier 3: Advanced Concepts',
    concepts: ['OOP', 'Error Handling'],
    description: 'Master classes, inheritance, and bulletproof applications.'
  }
]

export default function DashboardPage() {
  const { token, user } = useAuth()
  const { mastery, refreshMastery, getMasteryScore, getWeakestConcept } = useMastery()
  const navigate = useNavigate()

  const [events, setEvents] = useState([])
  const [eventsLoading, setEventsLoading] = useState(true)
  const [copiedId, setCopiedId] = useState(null)
  const [toastMessage, setToastMessage] = useState('')

  const fetchEvents = useCallback(async () => {
    if (!user?.id || !token) return
    try {
      const { data } = await axios.get('/api/learning-events', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setEvents(data)
    } catch {
      setEvents([])
    } finally {
      setEventsLoading(false)
    }
  }, [user?.id, token])

  useEffect(() => {
    refreshMastery()
    fetchEvents()
  }, [user?.id]) // eslint-disable-line

  // Build sparkline data per concept from learning events
  const sparklineData = (concept) => {
    return events
      .filter(e => e.concept_name === concept)
      .map(e => parseFloat(e.score || 0))
  }

  const weakest = getWeakestConcept()

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  const overallMastery = mastery.length
    ? Math.round(mastery.reduce((a, m) => a + (m.score || 0), 0) / mastery.length * 100)
    : 0

  // 1. Streak Info Calculation
  const getStreakInfo = () => {
    const activeDates = new Set()
    events.forEach(e => {
      activeDates.add(new Date(e.created_at).toDateString())
    })

    try {
      const chatLog = JSON.parse(localStorage.getItem('hcai_chat_activity_log') || '[]')
      chatLog.forEach(dateStr => activeDates.add(new Date(dateStr).toDateString()))
    } catch (e) { }

    const uniqueDates = Array.from(activeDates).map(d => new Date(d))
    uniqueDates.sort((a, b) => b - a)

    let streak = 0
    let today = new Date()
    today.setHours(0, 0, 0, 0)

    let yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    yesterday.setHours(0, 0, 0, 0)

    const hasActivity = (date) => {
      return uniqueDates.some(d => d.toDateString() === date.toDateString())
    }

    if (hasActivity(today) || hasActivity(yesterday)) {
      let current = hasActivity(today) ? today : yesterday
      streak = 1
      while (true) {
        let prev = new Date(current)
        prev.setDate(prev.getDate() - 1)
        if (hasActivity(prev)) {
          streak++
          current = prev
        } else {
          break
        }
      }
    }

    // Build weekly activity starting from Monday of this week
    const startOfWeek = new Date()
    const dayOfWeek = startOfWeek.getDay() // 0 = Sun, 1 = Mon, etc.
    const diff = startOfWeek.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1) // adjust when day is Sunday
    startOfWeek.setDate(diff)
    startOfWeek.setHours(0, 0, 0, 0)

    const weekly = []
    const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
    for (let i = 0; i < 7; i++) {
      const d = new Date(startOfWeek)
      d.setDate(d.getDate() + i)
      weekly.push({
        dayOfWeek: days[i],
        isActive: hasActivity(d)
      })
    }

    return { streak, weekly }
  }

  const { streak, weekly } = getStreakInfo()

  // 2. XP & Level System Calculation
  const getXPInfo = () => {
    const quizXP = events.reduce((sum, e) => sum + Math.round(parseFloat(e.score || 0) * 100), 0)
    const masteryXP = mastery.filter(m => (m.score || 0) >= 0.7).length * 150
    const questionCount = parseInt(localStorage.getItem('hcai_questions_asked') || '0', 10)
    const chatXP = questionCount * 10

    const totalXP = quizXP + masteryXP + chatXP + 100 // +100 base signing up XP
    const level = Math.floor(totalXP / 500) + 1
    const xpInLevel = totalXP % 500
    const xpNeeded = 500

    const titles = [
      'Syntax Seeker',
      'Variable Voyager',
      'Function Finder',
      'Loop Looker',
      'List Leader',
      'Logic Legend',
      'Class Commander',
      'Python Professor'
    ]
    const title = titles[Math.min(level - 1, titles.length - 1)]

    return { totalXP, level, xpInLevel, xpNeeded, title }
  }

  const { totalXP, level, xpInLevel, xpNeeded, title } = getXPInfo()

  // 3. Daily Goals Progress Calculation
  const getDailyGoalProgress = () => {
    const todayStr = new Date().toDateString()
    const quizzesToday = events.filter(e => new Date(e.created_at).toDateString() === todayStr).length
    const questionsToday = parseInt(localStorage.getItem(`hcai_questions_today_${todayStr}`) || '0', 10)

    // Complete 1 quiz or ask 3 questions
    let progressPct = 0
    if (quizzesToday >= 1) {
      progressPct = 100
    } else {
      progressPct = Math.min(Math.round((questionsToday / 3) * 100), 100)
    }

    return {
      progressPct,
      description: quizzesToday >= 1
        ? 'Daily goal completed! You solved a Python quiz.'
        : `Daily Goal: Complete 1 quiz or ask 3 questions today. (${questionsToday}/3 questions)`
    }
  }

  const { progressPct, description } = getDailyGoalProgress()

  // 4. Tier unlocking disabled: every tier is always accessible
  const getTierLockStatus = () => false

  const showNodeMessage = (concept, isLocked) => {
    if (isLocked) {
      setToastMessage(`🔒 Keep learning foundational Python basics to unlock ${concept}!`)
      setTimeout(() => setToastMessage(''), 3000)
    } else {
      navigate(`/quiz/${encodeURIComponent(concept)}`)
    }
  }


  return (
    <div className="dash-page">
      {/* Sidebar nav */}
      <nav className="dash-sidenav">
        <div className="dash-sidenav-logo">
          <span>🎓</span>
        </div>
        <button className="dash-nav-btn active" onClick={() => navigate('/dashboard')} title="Dashboard">
          <span>📊</span>
        </button>
        <button className="dash-nav-btn" onClick={() => navigate('/chat')} title="Tutor Chat">
          <span>💬</span>
        </button>
        <div style={{ flex: 1 }} />
        <button className="dash-nav-btn dash-nav-logout" onClick={() => navigate('/logout')} title="Sign Out">
          <span>🚪</span>
        </button>
      </nav>

      <div className="dash-scroll">
        <main className="dash-main">

          {/* Toast Message */}
          {toastMessage && (
            <div className="alert-error animate-fade-in" style={{ position: 'fixed', top: '16px', left: '50%', transform: 'translateX(-50%)', zIndex: 1000, margin: 0, boxShadow: 'var(--elevation-lg)' }}>
              <span>💡</span> {toastMessage}
            </div>
          )}

          {/* ── Header ── */}
          <div className="dash-header animate-fade-in">
            <div>
              <div className="dash-greeting-sub">{greeting()} 👋</div>
              <h1 className="dash-greeting-name">
                {user?.email?.split('@')[0] || 'Learner'}'s Progress
              </h1>
              <div className="dash-level-badge" data-level={level > 4 ? 'advanced' : level > 2 ? 'intermediate' : 'beginner'}>
                Level {level} · {title}
              </div>
            </div>
            <div className="dash-overall-ring">
              <RadialProgress score={overallMastery / 100} size={88} stroke={7} showPct />
              <span className="dash-overall-label">Overall Mastery</span>
            </div>
          </div>

          {/* ── Gamified Stats Grid ── */}
          <div className="dash-stats-grid animate-slide-up" style={{ animationDelay: '0.02s' }}>
            {/* Streak Card */}
            <div className="dash-stat-card">
              <div className="dash-stat-card-title">Weekly Streak</div>
              <div className="dash-stat-card-value" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                🔥 {streak} Day{streak !== 1 ? 's' : ''}
              </div>
              <div className="dash-heatmap">
                {weekly.map((w, idx) => (
                  <div key={idx} className={`dash-heatmap-day ${w.isActive ? 'active' : ''}`} title={`${w.dayOfWeek}: ${w.isActive ? 'Active' : 'No Activity'}`}>
                    <span className="dash-heatmap-day-label">{w.dayOfWeek}</span>
                    <div className="dash-heatmap-dot" />
                  </div>
                ))}
              </div>
            </div>

            {/* Daily Goal Card */}
            <div className="dash-stat-card">
              <div className="dash-stat-card-title">Daily Progress</div>
              <div className="dash-stat-card-value">{progressPct}%</div>
              <div className="dash-goal-progress">
                <div className="dash-goal-bar">
                  <div className="dash-goal-fill" style={{ width: `${progressPct}%`, background: 'linear-gradient(90deg, var(--indigo), var(--purple))' }} />
                </div>
                <div className="dash-goal-label">{description}</div>
              </div>
            </div>

            {/* XP Card */}
            <div className="dash-stat-card">
              <div className="dash-stat-card-title">XP Progression</div>
              <div className="dash-stat-card-value">{totalXP} XP</div>
              <div className="dash-goal-progress">
                <div className="dash-goal-bar">
                  <div className="dash-goal-fill" style={{ width: `${(xpInLevel / xpNeeded) * 100}%`, background: 'var(--green)' }} />
                </div>
                <div className="dash-goal-label">{xpNeeded - xpInLevel} XP until Level {level + 1}</div>
              </div>
            </div>
          </div>

          {/* ── Weakest concept CTA ── */}
          {weakest && (
            <div className="dash-callout animate-slide-up" style={{ animationDelay: '0.05s' }}>
              <div className="dash-callout-icon">💡</div>
              <div className="dash-callout-body">
                <div className="dash-callout-title">Strengthen: {weakest}</div>
                <div className="dash-callout-sub">
                  Your current mastery is {getMasteryScore(weakest)}%. Let's review loop types or complete a practice quiz!
                </div>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => navigate(`/quiz/${encodeURIComponent(weakest)}`)}
                id="btn-practice-weakest"
              >
                Practice →
              </button>
            </div>
          )}

          {/* ── Interactive Concept Skill Tree ── */}
          <h2 className="dash-section-title animate-slide-up" style={{ animationDelay: '0.1s' }}>
            Concept Skill Path
          </h2>

          <div className="dash-skill-tree animate-slide-up" style={{ animationDelay: '0.12s' }}>
            {TIERS.map((tier) => {
              const isLocked = getTierLockStatus(tier.id)
              return (
                <div key={tier.id} className="skill-tier" style={{ opacity: isLocked ? 0.6 : 1 }}>
                  <div className="skill-tier-header">
                    <span>{isLocked ? '🔒' : '🔑'}</span>
                    <span>{tier.name}</span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '-8px' }}>{tier.description}</p>

                  <div className="skill-nodes-grid">
                    {tier.concepts.map((concept) => {
                      const score = getMasteryScore(concept)
                      const rawScore = score / 100
                      const sparkData = sparklineData(concept)
                      const isNodeWeak = rawScore < 0.4 && !isLocked
                      const isNodeStrong = rawScore >= 0.7 && !isLocked

                      return (
                        <div
                          key={concept}
                          className={`skill-node ${isLocked ? 'node-locked' : ''} ${isNodeWeak ? 'node-weak' : ''} ${isNodeStrong ? 'node-strong' : ''}`}
                          onClick={() => showNodeMessage(concept, isLocked)}
                        >
                          {/* Color-blindness status indicators */}
                          {!isLocked && (
                            <span className={`node-status-badge ${isNodeStrong ? 'status-strong' : isNodeWeak ? 'status-weak' : 'status-amber'}`}>
                              {isNodeStrong ? '✓' : isNodeWeak ? '!' : '?'}
                            </span>
                          )}

                          <RadialProgress score={isLocked ? 0 : rawScore} size={52} stroke={4} showPct={!isLocked} />

                          <div className="dash-mastery-card-info" style={{ flex: 1 }}>
                            <div className="dash-mastery-card-name" style={{ fontSize: '0.9rem', fontWeight: '700' }}>
                              {CONCEPT_EMOJI[concept]} {concept}
                            </div>

                            {!isLocked && !eventsLoading && (
                              <div className="dash-mastery-card-trend" style={{ marginTop: '4px' }}>
                                <Sparkline
                                  data={sparkData.length ? sparkData : [rawScore * 0.6, rawScore * 0.8, rawScore]}
                                  width={60}
                                  height={16}
                                  color={isNodeStrong ? 'var(--green)' : rawScore >= 0.4 ? 'var(--cyan)' : 'var(--orange)'}
                                />
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>

          {/* ── Recent quiz history ── */}
          {events.length > 0 && (
            <>
              <h2 className="dash-section-title animate-slide-up" style={{ animationDelay: '0.2s' }}>
                Recent Activity
              </h2>
              <div className="dash-events animate-slide-up" style={{ animationDelay: '0.22s' }}>
                {events.slice(-8).reverse().map((e) => {
                  const pct = Math.round(parseFloat(e.score || 0) * 100)
                  return (
                    <div key={e.id} className="dash-event-row">
                      <span className="dash-event-concept">
                        {CONCEPT_EMOJI[e.concept_name] || '📝'} {e.concept_name}
                      </span>
                      <div className="dash-event-score-bar">
                        <div
                          className="dash-event-score-fill"
                          style={{ width: `${pct}%`, background: pct >= 80 ? 'var(--green)' : pct >= 50 ? 'var(--cyan)' : 'var(--orange)' }}
                        />
                      </div>
                      <span className="dash-event-pct">{pct}%</span>
                      <span className="dash-event-date">
                        {new Date(e.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {/* ── Quick actions ── */}
          <div className="dash-actions animate-slide-up" style={{ animationDelay: '0.28s' }}>
            <button className="btn btn-primary" onClick={() => navigate('/chat')} id="btn-open-tutor">
              💬 Ask AI Tutor
            </button>
          </div>

        </main>
      </div>
    </div>
  )
}

