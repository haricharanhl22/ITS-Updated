import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import DashboardPage  from './pages/DashboardPage'
import ChatPage       from './pages/ChatPage'
import QuizPage       from './pages/QuizPage'
import LoginPage      from './pages/LoginPage'
import LogoutPage     from './pages/LogoutPage'

import React, { useState, useEffect } from 'react'

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/logout" element={<ProtectedRoute><LogoutPage /></ProtectedRoute>} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/chat"      element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
      <Route path="/quiz/:concept" element={<ProtectedRoute><QuizPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('hcai_theme') || 'dark')
  const [dyslexia, setDyslexia] = useState(() => localStorage.getItem('hcai_dyslexia') === 'true')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('hcai_theme', theme)
  }, [theme])

  useEffect(() => {
    document.body.classList.toggle('dyslexia-font', dyslexia)
    localStorage.setItem('hcai_dyslexia', String(dyslexia))
  }, [dyslexia])

  return (
    <AuthProvider>
      <BrowserRouter>
        <div 
          className="accessibility-panel"
          style={{ 
            position: 'fixed', 
            top: '16px', 
            right: '16px', 
            zIndex: 10000, 
            display: 'flex', 
            gap: '8px' 
          }}
        >
          <button 
            type="button" 
            className="btn btn-ghost btn-sm"
            onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
            title="Toggle Light/Dark Theme"
            style={{ height: '36px', width: '36px', padding: '0', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '10px' }}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button 
            type="button" 
            className="btn btn-ghost btn-sm"
            onClick={() => setDyslexia(d => !d)}
            title="Toggle Dyslexia Friendly Font"
            style={{ height: '36px', padding: '0 12px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '10px', fontSize: '0.8rem', fontWeight: 'bold' }}
          >
            {dyslexia ? 'Standard Text' : 'OpenDyslexic'}
          </button>
        </div>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
