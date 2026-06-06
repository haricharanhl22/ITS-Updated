import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import BottomNav from '../components/BottomNav'
import './DashboardPage.css'

const GOALS = [
  { id: 1, title: 'Complete Python Basics lesson', sub: 'Lesson 3 of 5', xp: '+20 XP', done: true },
  { id: 2, title: 'Solve 3 coding challenges', sub: 'Challenges', xp: '+30 XP', done: false },
  { id: 3, title: 'Review AI Tutor feedback', sub: 'Personalised review', xp: '+10 XP', done: false },
]

const CODE_LINES = [
  { ln: 1, tokens: [{ t: 'kw', v: 'def ' }, { t: 'fn', v: 'greet' }, { t: 'pn', v: '(name):' }] },
  { ln: 2, tokens: [{ t: 'pn', v: '    ' }, { t: 'cm', v: '# Return a greeting message' }] },
  { ln: 3, tokens: [{ t: 'pn', v: '    ' }, { t: 'kw', v: 'return ' }, { t: 'str', v: 'f"Hello, {name}!"' }] },
  { ln: 4, tokens: [] },
  { ln: 5, tokens: [{ t: 'fn', v: 'print' }, { t: 'pn', v: '(' }, { t: 'fn', v: 'greet' }, { t: 'pn', v: '(' }, { t: 'str', v: '"World"' }, { t: 'pn', v: '))' }] },
]

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [goals, setGoals] = useState(GOALS)

  const toggleGoal = (id) => {
    setGoals(prev => prev.map(g => g.id === id ? { ...g, done: !g.done } : g))
  }

  const completedGoals = goals.filter(g => g.done).length

  return (
    <div className="dashboard-page">
      {/* Bottom / Side navigation */}
      <BottomNav activeTab="home" />

      <div className="dash-scroll">
        <main className="dash-main">

          {/* ── Header ── */}
          <div className="dash-header animate-fade-in">
            <div className="dash-greeting">
              <span className="dash-greeting-sub">{getGreeting()} 👋</span>
              <h1 className="dash-greeting-name">
                <span>{user?.username ?? 'Learner'}</span>!
              </h1>
            </div>

            <button
              className="dash-avatar-btn"
              id="nav-profile-btn"
              onClick={() => navigate('/logout')}
              title="Profile / Sign out"
            >
              <div className="dash-avatar">
                {user?.username?.[0]?.toUpperCase() ?? '?'}
              </div>
              <span className={`badge badge-${user?.role ?? 'student'}`}>{user?.role}</span>
            </button>
          </div>

          {/* ── Streak Card ── */}
          <div className="streak-card animate-slide-up" style={{ animationDelay: '0.05s' }}>
            <div className="streak-icon">🔥</div>
            <div className="streak-body">
              <div className="streak-label">Current Streak</div>
              <div className="streak-count">7 days</div>
              <div className="xp-bar-wrap">
                <div className="xp-bar">
                  <div className="xp-bar-fill" />
                </div>
                <span className="xp-label">360 / 500 XP</span>
              </div>
            </div>
          </div>

          {/* ── Stats Row ── */}
          <div className="stats-row animate-slide-up" style={{ animationDelay: '0.1s' }}>
            {[
              { icon: '📚', value: '12', label: 'Courses', trend: '+2 this week' },
              { icon: '🏆', value: '94%', label: 'Avg Score', trend: '↑ 3%' },
            ].map(s => (
              <div key={s.label} className="stat-card">
                <div className="stat-icon">{s.icon}</div>
                <div className="stat-value">{s.value}</div>
                <div className="stat-label">{s.label}</div>
                <div className="stat-trend">{s.trend}</div>
              </div>
            ))}
          </div>

          {/* ── Continue Learning ── */}
          <h2 className="section-heading animate-slide-up" style={{ animationDelay: '0.15s' }}>
            Continue Learning
          </h2>
          <div className="lesson-card animate-slide-up" style={{ animationDelay: '0.18s' }}>
            <div className="lesson-card-header">
              <span className="lesson-course-badge">Python</span>
              <span className="lesson-chapter">Chapter 3 · Functions</span>
            </div>
            <div className="lesson-title">Defining & Calling Functions</div>

            {/* Code Snippet */}
            <div className="code-snippet">
              <div className="code-snippet-bar">
                <span className="code-dot code-dot-red" />
                <span className="code-dot code-dot-yellow" />
                <span className="code-dot code-dot-green" />
                <span className="code-file-name">lesson.py</span>
              </div>
              <div className="code-body">
                {CODE_LINES.map((line) => (
                  <div key={line.ln} className="code-line">
                    <span className="code-ln">{line.ln}</span>
                    <span>
                      {line.tokens.map((tok, i) => (
                        <span key={i} className={tok.t}>{tok.v}</span>
                      ))}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Progress */}
            <div className="lesson-progress-row">
              <div className="lesson-progress-bar">
                <div className="lesson-progress-fill" />
              </div>
              <span className="lesson-progress-pct">68%</span>
            </div>

            <div className="lesson-card-footer">
              <button
                id="btn-continue-lesson"
                className="btn btn-primary btn-full btn-lg"
                onClick={() => {}}
              >
                Continue →
              </button>
            </div>
          </div>

          {/* ── Today's Goals ── */}
          <h2 className="section-heading animate-slide-up" style={{ animationDelay: '0.22s' }}>
            Today's Goals
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginLeft: '10px' }}>
              {completedGoals}/{goals.length} done
            </span>
          </h2>
          <div className="goals-list animate-slide-up" style={{ animationDelay: '0.25s' }}>
            {goals.map(goal => (
              <div
                key={goal.id}
                className={`goal-item ${goal.done ? 'done' : ''}`}
                onClick={() => toggleGoal(goal.id)}
                role="checkbox"
                aria-checked={goal.done}
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && toggleGoal(goal.id)}
              >
                <div className="goal-checkbox">
                  {goal.done && '✓'}
                </div>
                <div className="goal-text-wrap">
                  <div className="goal-title">{goal.title}</div>
                  <div className="goal-sub">{goal.sub}</div>
                </div>
                <span className="goal-xp">{goal.xp}</span>
              </div>
            ))}
          </div>

        </main>
      </div>
    </div>
  )
}
