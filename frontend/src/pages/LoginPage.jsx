import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { apiLogin, apiRegister, apiResendOtp, apiVerifyOtp } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import './LoginPage.css'

function extractError(err, fallback) {
  return err?.response?.data?.detail || err.message || fallback
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname ?? '/dashboard'
  const { isAuthenticated, isLoading: authLoading, login } = useAuth()

  // If a session is already active (e.g. left over from a previous account),
  // bounce straight to the app instead of letting the user sit on the
  // login/register screen while secretly still authenticated as someone
  // else — registering a "new" account without logging out first would
  // otherwise leave the old session untouched and just show the old
  // account's data.
  useEffect(() => {
    if (!authLoading && isAuthenticated) navigate(from, { replace: true })
  }, [isAuthenticated, authLoading, from, navigate])

  const [tab, setTab] = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPass, setShowPass] = useState(false)

  // Login form state
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })

  // Register form state
  const [regForm, setRegForm] = useState({ email: '', password: '', confirm: '' })

  // Set once registration succeeds — the backend has emailed a 6-digit OTP,
  // so the card swaps to an "enter your code" screen instead of navigating
  // straight in (there's no session yet until the OTP is verified).
  const [registrationSent, setRegistrationSent] = useState(false)
  const [resending, setResending] = useState(false)
  const [resendMsg, setResendMsg] = useState('')

  // OTP verification form state
  const [otp, setOtp] = useState('')
  const [verifying, setVerifying] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    if (!loginForm.email || !loginForm.password) {
      setError('Please fill in all fields.')
      return
    }
    setLoading(true)
    try {
      const { access_token } = await apiLogin(loginForm.email, loginForm.password)
      await login(access_token)
      navigate(from, { replace: true })
    } catch (err) {
      setError(extractError(err, 'Invalid credentials. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    if (!regForm.email || !regForm.password) {
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
      await apiRegister(regForm.email, regForm.password)
      // Account is created but unverified — the backend has emailed a
      // 6-digit OTP. There's no session yet, so show the code-entry screen
      // instead of navigating.
      setOtp('')
      setRegistrationSent(true)
    } catch (err) {
      setError(extractError(err, 'Registration failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async (e) => {
    e.preventDefault()
    setResendMsg('')
    if (!otp || otp.length !== 6) {
      setResendMsg('Enter the 6-digit code from your email.')
      return
    }
    setVerifying(true)
    try {
      const { access_token } = await apiVerifyOtp(regForm.email, otp)
      await login(access_token)
      navigate(from, { replace: true })
    } catch (err) {
      setResendMsg(extractError(err, 'Invalid or expired code. Please try again.'))
    } finally {
      setVerifying(false)
    }
  }

  const handleResendVerification = async () => {
    setResending(true)
    setResendMsg('')
    try {
      await apiResendOtp(regForm.email)
      setResendMsg('A new code has been sent — check your inbox.')
    } catch (err) {
      setResendMsg(extractError(err, 'Could not resend the code. Please try again shortly.'))
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="login-page">
      {/* Brand */}
      <div className="login-brand animate-fade-in">
        <div className="login-logo-ring">🎓</div>
        <span className="login-app-name">HCAI-ITS</span>
        <span className="login-tagline">Intelligent Tutoring System</span>
      </div>

      <div className="login-container animate-fade-in-up">

        {registrationSent ? (
          /* ── Enter OTP ── */
          <div className="verify-email-panel animate-fade-in">
            <div className="verify-email-icon">📬</div>
            <h2 className="verify-email-title">Check your inbox</h2>
            <p className="verify-email-text">
              We've sent a 6-digit verification code to <strong>{regForm.email}</strong>.
              Enter it below to activate your account.
            </p>

            <form id="otp-form" onSubmit={handleVerifyOtp} className="auth-form">
              <div className="form-group">
                <label className="form-label" htmlFor="otp-input">Verification code</label>
                <input
                  id="otp-input"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                  className="input-field"
                  placeholder="123456"
                  value={otp}
                  onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  disabled={verifying}
                />
              </div>

              {resendMsg && <div className="verify-email-resend-msg animate-fade-in">{resendMsg}</div>}

              <div className="verify-email-actions">
                <button
                  id="btn-verify-otp"
                  type="submit"
                  className="btn btn-primary btn-full btn-lg btn-submit"
                  disabled={verifying}
                >
                  {verifying ? <span className="spinner" /> : null}
                  {verifying ? 'Verifying…' : 'Verify & Continue →'}
                </button>
                <button
                  id="btn-resend-verification"
                  type="button"
                  className="btn btn-outline btn-full"
                  onClick={handleResendVerification}
                  disabled={resending}
                >
                  {resending ? <span className="spinner" style={{ width: 14, height: 14 }} /> : null}
                  {resending ? 'Resending…' : 'Resend code'}
                </button>
                <button
                  id="btn-back-to-signin"
                  type="button"
                  className="btn btn-ghost btn-full"
                  onClick={() => {
                    setRegistrationSent(false)
                    setResendMsg('')
                    setOtp('')
                    setTab('login')
                    setError('')
                  }}
                >
                  Back to Sign In
                </button>
              </div>
            </form>
          </div>
        ) : (
        <>
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
              <label className="form-label" htmlFor="login-email">Email</label>
              <div className="input-wrap">
                <span className="input-icon">✉</span>
                <input
                  id="login-email"
                  type="email"
                  className="input-field with-icon"
                  placeholder="your@email.com"
                  autoComplete="email"
                  value={loginForm.email}
                  onChange={e => setLoginForm(f => ({ ...f, email: e.target.value }))}
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
        </>
        )}
      </div>

      <p className="login-footer-note">
        HCAI Intelligent Tutoring System · v1.0
      </p>
    </div>
  )
}
