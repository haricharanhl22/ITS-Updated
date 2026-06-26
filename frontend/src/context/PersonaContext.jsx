/**
 * PersonaContext.jsx
 * Manages the selected demo persona. Replaces authentication for the demo flow.
 * Stores: { studentId, username, displayName, level, emoji, tagline, token, mastery }
 */
import React, { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'

const PersonaContext = createContext(null)

const STORAGE_KEY = 'hcai_persona'

export const CONCEPTS = [
  'Variables', 'Functions', 'Loops', 'OOP',
  'Strings', 'Lists', 'Dictionaries', 'Error Handling',
]

export function PersonaProvider({ children }) {
  const [persona, setPersona] = useState(null)
  const [mastery, setMastery]  = useState([])
  const [loading, setLoading]  = useState(true)

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setPersona(parsed)
        if (parsed?.studentId && parsed?.token) {
          fetchMastery(parsed.studentId, parsed.token)
        }
      } catch {
        localStorage.removeItem(STORAGE_KEY)
      }
    }
    setLoading(false)
  }, [])

  const fetchMastery = async (studentId, token) => {
    try {
      const { data } = await axios.get(`/mastery/${studentId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setMastery(data)
    } catch {
      setMastery([])
    }
  }

  const selectPersona = async (level) => {
    const { data } = await axios.post('/demo/login', { persona: level })
    const p = {
      studentId:   data.student_id,
      username:    data.username,
      displayName: data.display_name,
      level:       data.level,
      emoji:       data.emoji,
      tagline:     data.tagline,
      token:       data.access_token,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p))
    setPersona(p)
    await fetchMastery(p.studentId, p.token)
    return p
  }

  const clearPersona = () => {
    localStorage.removeItem(STORAGE_KEY)
    setPersona(null)
    setMastery([])
  }

  const refreshMastery = () => {
    if (persona?.studentId && persona?.token) {
      fetchMastery(persona.studentId, persona.token)
    }
  }

  // Mastery helpers
  const getMasteryScore = (concept) => {
    const entry = mastery.find(m => m.concept === concept)
    return entry ? Math.round((entry.score || 0) * 100) : 0
  }

  const getWeakestConcept = () => {
    if (!mastery.length) return 'Variables'
    return mastery.reduce((a, b) => (a.score < b.score ? a : b)).concept
  }

  const token  = persona?.token  ?? null
  const userId = persona?.studentId ?? null

  return (
    <PersonaContext.Provider value={{
      persona, mastery, loading, token, userId,
      selectPersona, clearPersona, refreshMastery,
      getMasteryScore, getWeakestConcept,
      isSelected: !!persona,
    }}>
      {children}
    </PersonaContext.Provider>
  )
}

export function usePersona() {
  const ctx = useContext(PersonaContext)
  if (!ctx) throw new Error('usePersona must be used inside PersonaProvider')
  return ctx
}
