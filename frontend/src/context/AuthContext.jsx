import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiLogout } from '../api/auth'

const AuthContext = createContext(null)

const TOKEN_KEY = 'hcai_token'
const USER_KEY  = 'hcai_user'

export function AuthProvider({ children }) {
  const [state, setState] = useState({
    token: null,
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser  = localStorage.getItem(USER_KEY)
    if (savedToken && savedUser) {
      try {
        const user = JSON.parse(savedUser)
        setState({ token: savedToken, user, isAuthenticated: true, isLoading: false })
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setState(s => ({ ...s, isLoading: false }))
      }
    } else {
      setState(s => ({ ...s, isLoading: false }))
    }
  }, [])

  const login = (token, user) => {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState({ token, user, isAuthenticated: true, isLoading: false })
  }

  const logout = async () => {
    if (state.token) {
      try { await apiLogout(state.token) } catch { /* ignore */ }
    }
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setState({ token: null, user: null, isAuthenticated: false, isLoading: false })
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
