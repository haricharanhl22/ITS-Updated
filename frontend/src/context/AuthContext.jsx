import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiLogout, apiMe } from '../api/auth'

const AuthContext = createContext(null)

const TOKEN_KEY = 'its_token'

export function AuthProvider({ children }) {
  const [state, setState] = useState({
    token: localStorage.getItem(TOKEN_KEY),
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setState(s => ({ ...s, isLoading: false }))
      return
    }
    apiMe(token)
      .then(user => setState({ token, user, isAuthenticated: true, isLoading: false }))
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        setState({ token: null, user: null, isAuthenticated: false, isLoading: false })
      })
  }, [])

  // Called after login/verify-otp succeeds with a fresh access token.
  const login = async (token) => {
    localStorage.setItem(TOKEN_KEY, token)
    const user = await apiMe(token)
    setState({ token, user, isAuthenticated: true, isLoading: false })
    return user
  }

  const logout = async () => {
    const { token } = state
    localStorage.removeItem(TOKEN_KEY)
    setState({ token: null, user: null, isAuthenticated: false, isLoading: false })
    if (token) {
      try { await apiLogout(token) } catch { /* best-effort */ }
    }
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
