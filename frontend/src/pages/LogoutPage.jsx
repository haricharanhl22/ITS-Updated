import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './LogoutPage.css'

export default function LogoutPage() {
  const { logout, user, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [countdown, setCountdown] = useState(5)
  const [loggingOut, setLoggingOut] = useState(false)

  // If not authenticated, redirect to login immediately
  useEffect(() => {
    if (!isAuthenticated) navigate('/login', { replace: true })
  }, [isAuthenticated, navigate])

  // Auto-logout countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) {
          clearInterval(timer)
          handleLogout()
          return 0
        }
        return c - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const handleLogout = async () => {
    if (loggingOut) return
    setLoggingOut(true)
    await logout()
    navigate('/login', { replace: true })
  }

  const cancelLogout = () => {
    navigate(-1)
  }

  return (
    <div className="logout-page">
      <div className="orb orb-logout-1" />
      <div className="orb orb-logout-2" />

      <div className="logout-card animate-fade-in-up">
        <div className="logout-icon-wrap">
          <div className="logout-icon">👋</div>
        </div>

        <h1 className="logout-title">Signing out</h1>
        <p className="logout-user">
          Goodbye, <span className="username-highlight">{user?.username}</span>!
        </p>
        <p className="logout-sub">You will be signed out automatically in:</p>

        {/* Countdown ring */}
        <div className="countdown-ring" aria-label={`${countdown} seconds remaining`}>
          <svg viewBox="0 0 56 56" className="ring-svg">
            <circle className="ring-bg" cx="28" cy="28" r="24" />
            <circle
              className="ring-fill"
              cx="28"
              cy="28"
              r="24"
              style={{
                strokeDashoffset: `${(1 - countdown / 5) * 151}`,
              }}
            />
          </svg>
          <span className="ring-number">{countdown}</span>
        </div>

        <div className="logout-actions">
          <button
            id="btn-confirm-logout"
            type="button"
            className="btn btn-danger btn-full"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? <span className="spinner" /> : ''}
            {loggingOut ? 'Signing out…' : 'Sign Out Now'}
          </button>
          <button
            id="btn-cancel-logout"
            type="button"
            className="btn btn-ghost btn-full"
            onClick={cancelLogout}
            disabled={loggingOut}
          >
            Cancel — Stay Logged In
          </button>
        </div>

        <div className="session-info">
          <div className="session-row">
            <span className="session-key">Role</span>
            <span className={`badge badge-${user?.role}`}>{user?.role}</span>
          </div>
          <div className="session-row">
            <span className="session-key">Email</span>
            <span className="session-val">{user?.email}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
