import { useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { apiLogin, apiMe, apiRegister, apiVerifyOtp } from '../api/auth'
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

  // OTP verification state
  const [otpStep, setOtpStep] = useState(false)
  const [pendingEmail, setPendingEmail] = useState('')
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', ''])
  const otpRefs = useRef([])

  // Login form state
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })

  // Register form state
  const [regForm, setRegForm] = useState({
    username: '', email: '', password: '', confirm: '',
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
      setError(err?.response?.data?.detail ?? 'Invalid credentials. Please try again.')
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
      const res = await apiRegister(regForm.username, regForm.email, regForm.password, 'student')
      setPendingEmail(res.email)
      setOtpDigits(['', '', '', '', '', ''])
      setOtpStep(true)
      setError('')
    } catch (err) {
      setError(err?.response?.data?.detail ?? 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleOtpChange = (index, value) => {
    if (!/^\d?$/.test(value)) return
    const next = [...otpDigits]
    next[index] = value
    setOtpDigits(next)
    if (value && index < 5) otpRefs.current[index + 1]?.focus()
  }

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpRefs.current[index - 1]?.focus()
    }
  }

  const handleOtpPaste = (e) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    const next = [...otpDigits]
    for (let i = 0; i < 6; i++) next[i] = pasted[i] ?? ''
    setOtpDigits(next)
    otpRefs.current[Math.min(pasted.length, 5)]?.focus()
  }

  const handleVerifyOtp = async (e) => {
    e.preventDefault()
    setError('')
    const otp = otpDigits.join('')
    if (otp.length !== 6) {
      setError('Please enter the full 6-digit code.')
      return
    }
    setLoading(true)
    try {
      const tokenData = await apiVerifyOtp(pendingEmail, otp)
      const userData  = await apiMe(tokenData.access_token)
      login(tokenData.access_token, userData)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail ?? 'Invalid or expired OTP. Please try again.')
      setOtpDigits(['', '', '', '', '', ''])
      otpRefs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  // ── OTP SCREEN ────────────────────────────────────────────────────────────
  if (otpStep) {
    return (
      <div className="login-page">
        <div className="login-brand">
          <div className="login-logo-ring">🎓</div>
          <span className="login-app-name">HCAI-ITS</span>
        </div>

        <div className="login-container animate-fade-in-up">
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div style={{ fontSize: '40px', marginBottom: '12px' }}>✉️</div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text)', marginBottom: '8px' }}>
              Check your email
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              We sent a 6-digit code to<br />
              <strong style={{ color: 'var(--indigo-light)' }}>{pendingEmail}</strong>
            </p>
          </div>

          {error && (
            <div className="alert-error animate-fade-in" role="alert">
              <span>⚠</span> {error}
            </div>
          )}

          <form id="otp-form" onSubmit={handleVerifyOtp} className="auth-form animate-fade-in">
            {/* 6-digit OTP boxes */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '8px' }}>
              {otpDigits.map((digit, i) => (
                <input
                  key={i}
                  ref={el => otpRefs.current[i] = el}
                  id={`otp-digit-${i}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={e => handleOtpChange(i, e.target.value)}
                  onKeyDown={e => handleOtpKeyDown(i, e)}
                  onPaste={i === 0 ? handleOtpPaste : undefined}
                  disabled={loading}
                  style={{
                    width: '48px',
                    height: '58px',
                    textAlign: 'center',
                    fontSize: '1.6rem',
                    fontWeight: 800,
                    fontFamily: 'var(--font)',
                    borderRadius: '14px',
                    border: `2px solid ${digit ? 'var(--indigo)' : 'var(--border)'}`,
                    background: digit ? 'var(--indigo-subtle)' : 'var(--bg)',
                    color: 'var(--text)',
                    outline: 'none',
                    transition: 'all var(--ease)',
                    boxShadow: digit ? '0 0 0 4px var(--indigo-subtle)' : 'none',
                  }}
                />
              ))}
            </div>

            <button
              id="btn-verify-otp"
              type="submit"
              className="btn btn-primary btn-full btn-lg btn-submit"
              disabled={loading || otpDigits.join('').length !== 6}
            >
              {loading ? <span className="spinner" /> : null}
              {loading ? 'Verifying…' : 'Verify & Continue →'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <button
              type="button"
              style={{
                background: 'none', border: 'none',
                color: 'var(--text-muted)', cursor: 'pointer',
                fontSize: '0.85rem', fontFamily: 'var(--font)',
              }}
              onClick={() => { setOtpStep(false); setTab('register'); setError('') }}
            >
              ← Back to registration
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── MAIN LOGIN / REGISTER SCREEN ─────────────────────────────────────────
  return (
    <div className="login-page">
      {/* Brand */}
      <div className="login-brand animate-fade-in">
        <div className="login-logo-ring">🎓</div>
        <span className="login-app-name">HCAI-ITS</span>
        <span className="login-tagline">Intelligent Tutoring System</span>
      </div>

      <div className="login-container animate-fade-in-up">

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
              <label className="form-label" htmlFor="login-username">Username or Email</label>
              <div className="input-wrap">
                <span className="input-icon">👤</span>
                <input
                  id="login-username"
                  type="text"
                  className="input-field with-icon"
                  placeholder="Enter username or email"
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
              className="btn btn-primary btn-full btn-lg btn-submit"
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : null}
              {loading ? 'Signing in…' : 'Sign In →'}
            </button>
          </form>
        )}

        {/* ── REGISTER FORM ── */}
        {tab === 'register' && (
          <form id="register-form" onSubmit={handleRegister} className="auth-form animate-fade-in">
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
              className="btn btn-primary btn-full btn-lg btn-submit"
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : null}
              {loading ? 'Creating account…' : 'Create Account →'}
            </button>
          </form>
        )}

        {/* Demo Accounts */}
        <div className="login-divider">
          <div className="login-divider-line" />
          <span className="login-divider-text">Quick Demo</span>
          <div className="login-divider-line" />
        </div>

        <div className="demo-section">
          <div className="demo-grid">
            {[
              { label: 'Admin', username: 'admin', password: 'admin123', badge: 'admin' },
              { label: 'Student', username: 'student', password: 'student123', badge: 'student' },
            ].map(d => (
              <button
                key={d.label}
                id={`demo-${d.badge}`}
                type="button"
                className={`demo-btn badge-${d.badge}`}
                onClick={() => {
                  setTab('login')
                  setOtpStep(false)
                  setLoginForm({ username: d.username, password: d.password })
                  setError('')
                }}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <p className="login-footer-note">
        HCAI Intelligent Tutoring System · v1.0
      </p>
    </div>
  )
}
