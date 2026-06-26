import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import MasteryBar from './MasteryBar'
import './Sidebar.css'

/**
 * Sidebar — collapsible left panel showing concept mastery and navigation.
 *
 * Props:
 *   mastery        {Array}   [{ concept, score }]
 *   activeConcept  {string}  currently detected concept from chat
 *   onQuiz         {fn}      (concept) => navigate to quiz
 *   collapsed      {boolean}
 *   onToggle       {fn}
 */
export default function Sidebar({
  mastery = [],
  activeConcept = null,
  onQuiz,
  collapsed,
  onToggle,
}) {
  const { user } = useAuth()
  const navigate  = useNavigate()
  const location  = useLocation()

  const isChat      = location.pathname === '/chat'
  const isDashboard = location.pathname === '/dashboard'

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} aria-label="Navigation sidebar">

      {/* ── Header ── */}
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <span className="sidebar-logo">🎓</span>
          <span className="sidebar-title">HCAI-ITS</span>
        </div>
        <button
          className="sidebar-toggle"
          onClick={onToggle}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          id="btn-sidebar-toggle"
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      {/* ── Body ── */}
      <div className="sidebar-body">

        {/* Nav links */}
        <button
          className={`sidebar-nav-link ${isDashboard ? 'active' : ''}`}
          onClick={() => navigate('/dashboard')}
          id="sidebar-nav-dashboard"
        >
          <span className="nav-link-icon">🏠</span>
          <span className="nav-link-text">Dashboard</span>
        </button>

        <button
          className={`sidebar-nav-link ${isChat ? 'active' : ''}`}
          onClick={() => navigate('/chat')}
          id="sidebar-nav-chat"
        >
          <span className="nav-link-icon">🤖</span>
          <span className="nav-link-text">AI Tutor</span>
        </button>

        {/* Concepts */}
        <div className="sidebar-section-label">📚 Concepts</div>

        {mastery.length === 0 ? (
          <div className="sidebar-empty">
            Ask a question to start tracking mastery.
          </div>
        ) : (
          mastery.map(({ concept, score }) => (
            <div
              key={concept}
              className={`sidebar-concept ${activeConcept === concept ? 'active' : ''}`}
            >
              <div className="sidebar-concept-row">
                <span className="sidebar-concept-name">{concept}</span>
                <button
                  className="sidebar-quiz-btn"
                  onClick={() => onQuiz(concept)}
                  id={`btn-quiz-${concept.toLowerCase().replace(/\s+/g, '-')}`}
                  aria-label={`Take quiz for ${concept}`}
                >
                  Quiz →
                </button>
              </div>
              <MasteryBar score={score} showPct={false} />
            </div>
          ))
        )}
      </div>

      {/* ── Footer ── */}
      <div className="sidebar-footer">
        <div className="sidebar-avatar">
          {user?.username?.[0]?.toUpperCase() ?? '?'}
        </div>
        <div className="sidebar-user-info">
          <div className="sidebar-username">{user?.username ?? 'Student'}</div>
          <div className="sidebar-role">{user?.role ?? 'student'}</div>
        </div>
      </div>
    </aside>
  )
}
