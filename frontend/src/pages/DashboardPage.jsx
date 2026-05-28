import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './DashboardPage.css'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="dashboard-page">
      <div className="orb orb-dash-1" />
      <div className="orb orb-dash-2" />

      {/* Top nav */}
      <nav className="dash-nav glass animate-fade-in">
        <div className="nav-brand">
          <span className="nav-logo">🎓</span>
          <span className="nav-title">HCAI-ITS</span>
        </div>
        <div className="nav-right">
          <div className="nav-user">
            <div className="avatar">{user?.username?.[0]?.toUpperCase()}</div>
            <div className="nav-user-info">
              <span className="nav-username">{user?.username}</span>
              <span className={`badge badge-${user?.role}`}>{user?.role}</span>
            </div>
          </div>
          <Link to="/logout" id="nav-logout-btn" className="btn btn-ghost btn-sm">
            Sign Out
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="dash-main">
        <div className="hero animate-fade-in-up">
          <div className="hero-badge">
            <span className="pulse-dot" /> Live Session
          </div>
          <h1 className="hero-title">
            Welcome back,<br />
            <span className="gradient-text">{user?.username}</span>!
          </h1>
          <p className="hero-sub">
            Your intelligent tutoring dashboard is ready. Continue your learning journey.
          </p>
        </div>

        {/* Stats grid */}
        <div className="stats-grid animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          {[
            { icon: '📚', label: 'Courses', value: '12', trend: '+2 this week' },
            { icon: '⚡', label: 'Sessions', value: '48', trend: '+6 today' },
            { icon: '🏆', label: 'Score', value: '94%', trend: '↑ 3% from last week' },
            { icon: '⏱', label: 'Study Time', value: '28h', trend: 'This month' },
          ].map(s => (
            <div key={s.label} className="stat-card glass">
              <div className="stat-icon">{s.icon}</div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
              <div className="stat-trend">{s.trend}</div>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="actions-section animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <h2 className="section-title">Quick Actions</h2>
          <div className="actions-grid">
            {[
              { icon: '📖', title: 'Start Learning', desc: 'Jump into your next lesson', color: 'primary' },
              { icon: '📊', title: 'View Progress', desc: 'Track your performance', color: 'secondary' },
              { icon: '🤖', title: 'AI Tutor', desc: 'Get personalized help', color: 'accent' },
              { icon: '📋', title: 'Assignments', desc: 'Check pending tasks', color: 'success' },
            ].map(a => (
              <div key={a.title} className={`action-card action-${a.color}`}>
                <div className="action-icon">{a.icon}</div>
                <div className="action-text">
                  <div className="action-title">{a.title}</div>
                  <div className="action-desc">{a.desc}</div>
                </div>
                <div className="action-arrow">→</div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
