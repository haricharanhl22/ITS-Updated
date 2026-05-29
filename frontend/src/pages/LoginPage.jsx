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
  const [otpStep, setOtpStep] = useState(false)   // true = show OTP screen
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
      const res = await apiRegister(regForm.username, regForm.email, regForm.password, 'student')
      // Backend now sends OTP email instead of a token
      setPendingEmail(res.email)
      setOtpDigits(['', '', '', '', '', ''])
      setOtpStep(true)
      setError('')
    } catch (err) {
      const msg = err?.response?.data?.detail
      setError(msg ?? 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // OTP digit input handlers
  const handleOtpChange = (index, value) => {
    if (!/^\d?$/.test(value)) return
    const next = [...otpDigits]
    next[index] = value
    setOtpDigits(next)
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus()
    }
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
      const msg = err?.response?.data?.detail
      setError(msg ?? 'Invalid or expired OTP. Please try again.')
      setOtpDigits(['', '', '', '', '', ''])
      otpRefs.current[0]?.focus()
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
    setOtpStep(false)
    setLoginForm({ username: d.username, password: d.password })
    setError('')
  }

  // ── OTP VERIFICATION SCREEN ──────────────────────────────────────────────
  if (otpStep) {
    return (
      <div className="login-page">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />

        <div className="login-container animate-fade-in-up">
          <div className="login-header">
            <div className="logo-wrap">
              <div className="logo-icon">✉️</div>
            </div>
            <p className="login-subtitle">Check your email</p>
          </div>

          <div style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--text-muted, #9ca3af)', fontSize: '0.9rem' }}>
            We sent a 6-digit code to<br />
            <strong style={{ color: 'var(--text, #e5e7eb)' }}>{pendingEmail}</strong>
          </div>

          {error && (
            <div className="alert-error animate-fade-in" role="alert">
              <span>⚠</span> {error}
            </div>
          )}

          <form id="otp-form" onSubmit={handleVerifyOtp} className="auth-form animate-fade-in">
            {/* 6-digit OTP boxes */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '1.5rem' }}>
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
                    height: '56px',
                    textAlign: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    borderRadius: '10px',
                    border: '2px solid var(--border, rgba(255,255,255,0.12))',
                    background: 'var(--input-bg, rgba(255,255,255,0.07))',
                    color: 'var(--text, #e5e7eb)',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                />
              ))}
            </div>

            <button
              id="btn-verify-otp"
              type="submit"
              className="btn btn-primary btn-full btn-lg"
              disabled={loading || otpDigits.join('').length !== 6}
            >
              {loading ? <span className="spinner" /> : ''}
              {loading ? 'Verifying…' : 'Verify & Continue'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <button
              type="button"
              style={{ background: 'none', border: 'none', color: 'var(--text-muted, #9ca3af)', cursor: 'pointer', fontSize: '0.85rem' }}
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
