import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { supabase } from '../api/supabaseClient'
import './LoginPage.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname ?? '/dashboard'

  const [tab, setTab] = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPass, setShowPass] = useState(false)

  // Login form state
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })

  // Register form state
  const [regForm, setRegForm] = useState({ email: '', password: '', confirm: '' })

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    if (!loginForm.email || !loginForm.password) {
      setError('Please fill in all fields.')
      return
    }
    setLoading(true)
    try {
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email: loginForm.email,
        password: loginForm.password,
      })
      if (signInError) throw signInError
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please try again.')
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
      const { error: signUpError } = await supabase.auth.signUp({
        email: regForm.email,
        password: regForm.password,
      })
      if (signUpError) throw signUpError
      // For Supabase, if email confirmation is disabled, user is logged in automatically.
      // If enabled, they will need to check their email. For this patch, we assume success routes to dashboard.
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
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
      </div>

      <p className="login-footer-note">
        HCAI Intelligent Tutoring System · v1.0
      </p>
    </div>
  )
}
