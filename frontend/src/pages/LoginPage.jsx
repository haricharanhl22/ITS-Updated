import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { apiLogin, apiMe, apiRegister } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import './LoginPage.css'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname ?? '/dashboard'

  const [tab, setTab] = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPass, setShowPass] = useState(false)

  // Login form state
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })

  // Register form state
  const [regForm, setRegForm] = useState({
    username: '', email: '', password: '', confirm: '', role: 'student',
  })

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    if (!loginForm.username || !loginForm.password) {
      setError('Please fill in all fields.')
      return
    }
    setLoading(true)
    try {
      const tokenData = await apiLogin(loginForm.username, loginForm.password)
      const userData  = await apiMe(tokenData.access_token)
      login(tokenData.access_token, userData)
      navigate(from, { replace: true })
    } catch (err) {
      const msg = err?.response?.data?.detail
      setError(msg ?? 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    if (!regForm.username || !regForm.email || !regForm.password) {
      setError('Please fill in all fields.')
      return
    }
    if (regForm.password !== regForm.confirm) {
      setError('Passwords do not match.')
      return
    }
    if (regForm.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setLoading(true)
    try {
      const tokenData = await apiRegister(regForm.username, regForm.email, regForm.password, regForm.role)
      const userData  = await apiMe(tokenData.access_token)
      login(tokenData.access_token, userData)
      navigate(from, { replace: true })
    } catch (err) {
      const msg = err?.response?.data?.detail
      setError(msg ?? 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const demoAccounts = [
    { label: 'Admin', username: 'admin', password: 'admin123', badge: 'admin' },
    { label: 'Student', username: 'student', password: 'student123', badge: 'student' },
  ]

  const fillDemo = (d) => {
    setTab('login')
    setLoginForm({ username: d.username, password: d.password })
    setError('')
  }

  return (
    <div className="login-page">
      {/* Decorative background orbs */}
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />

      <div className="login-container animate-fade-in-up">

        {/* Header */}
        <div className="login-header">
          <div className="logo-wrap">
            <div className="logo-icon">🎓</div>
          </div>
          <p className="login-subtitle">Intelligent Tutoring System</p>
        </div>

        {/* Tabs */}
        <div className="tab-bar" role="tablist">
          <button
            id="tab-login"
            role="tab"
            aria-selected={tab === 'login'}
            className={`tab-btn ${tab === 'login' ? 'active' : ''}`}
            onClick={() => { setTab('login'); setError('') }}
          >
            Sign In
          </button>
          <button
            id="tab-register"
            role="tab"
            aria-selected={tab === 'register'}
            className={`tab-btn ${tab === 'register' ? 'active' : ''}`}
            onClick={() => { setTab('register'); setError('') }}
          >
            Register
          </button>
          <div className={`tab-indicator ${tab === 'register' ? 'right' : ''}`} />
        </div>

        {/* Error banner */}
        {error && (
          <div className="alert-error animate-fade-in" role="alert">
            <span>⚠</span> {error}
          </div>
        )}

        {/* ── LOGIN FORM ── */}
        {tab === 'login' && (
          <form id="login-form" onSubmit={handleLogin} className="auth-form animate-fade-in">
            <div className="form-group">
              <label className="form-label" htmlFor="login-username">Username</label>
              <div className="input-wrap">
                <span className="input-icon">👤</span>
                <input
                  id="login-username"
                  type="text"
                  className="input-field with-icon"
                  placeholder="Enter your username"
                  autoComplete="username"
                  value={loginForm.username}
                  onChange={e => setLoginForm(f => ({ ...f, username: e.target.value }))}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="login-password">Password</label>
              <div className="input-wrap">
                <span className="input-icon">🔒</span>
                <input
                  id="login-password"
                  type={showPass ? 'text' : 'password'}
                  className="input-field with-icon with-icon-right"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  value={loginForm.password}
                  onChange={e => setLoginForm(f => ({ ...f, password: e.target.value }))}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="pass-toggle"
                  onClick={() => setShowPass(v => !v)}
                  aria-label="Toggle password visibility"
                >
                  {showPass ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            <button
              id="btn-login"
              type="submit"
              className="btn btn-primary btn-full btn-lg"
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : ''}
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        )}

        {/* ── REGISTER FORM ── */}
        {tab === 'register' && (
          <form id="register-form" onSubmit={handleRegister} className="auth-form animate-fade-in">
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label" htmlFor="reg-username">Username</label>
                <div className="input-wrap">
                  <span className="input-icon">👤</span>
                  <input
                    id="reg-username"
                    type="text"
                    className="input-field with-icon"
                    placeholder="Choose a username"
                    autoComplete="username"
                    value={regForm.username}
                    onChange={e => setRegForm(f => ({ ...f, username: e.target.value }))}
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="reg-role">Role</label>
                <select
                  id="reg-role"
                  className="input-field"
                  value={regForm.role}
                  onChange={e => setRegForm(f => ({ ...f, role: e.target.value }))}
                  disabled={loading}
                >
                  <option value="student">Student</option>
                  <option value="teacher">Teacher</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="reg-email">Email</label>
              <div className="input-wrap">
                <span className="input-icon">✉</span>
                <input
                  id="reg-email"
                  type="email"
                  className="input-field with-icon"
                  placeholder="your@email.com"
                  autoComplete="email"
                  value={regForm.email}
                  onChange={e => setRegForm(f => ({ ...f, email: e.target.value }))}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="reg-password">Password</label>
              <div className="input-wrap">
                <span className="input-icon">🔒</span>
                <input
                  id="reg-password"
                  type={showPass ? 'text' : 'password'}
                  className="input-field with-icon with-icon-right"
                  placeholder="Min 6 characters"
                  autoComplete="new-password"
                  value={regForm.password}
                  onChange={e => setRegForm(f => ({ ...f, password: e.target.value }))}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="pass-toggle"
                  onClick={() => setShowPass(v => !v)}
                  aria-label="Toggle password visibility"
                >
                  {showPass ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="reg-confirm">Confirm Password</label>
              <div className="input-wrap">
                <span className="input-icon">🔒</span>
                <input
                  id="reg-confirm"
                  type={showPass ? 'text' : 'password'}
                  className={`input-field with-icon ${regForm.confirm && regForm.confirm !== regForm.password ? 'error' : ''}`}
                  placeholder="Repeat password"
                  autoComplete="new-password"
                  value={regForm.confirm}
                  onChange={e => setRegForm(f => ({ ...f, confirm: e.target.value }))}
                  disabled={loading}
                />
              </div>
            </div>

            <button
              id="btn-register"
              type="submit"
              className="btn btn-primary btn-full btn-lg"
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : ''}
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>
        )}

        {/* Demo Accounts */}
        <div className="demo-section">
          <p className="demo-label">Quick demo access</p>
          <div className="demo-grid">
            {demoAccounts.map(d => (
              <button
                key={d.label}
                id={`demo-${d.badge}`}
                type="button"
                className={`demo-btn badge-${d.badge}`}
                onClick={() => fillDemo(d)}
                title={`Login as ${d.label}`}
              >
                <span className={`badge badge-${d.badge}`}>{d.label}</span>
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
