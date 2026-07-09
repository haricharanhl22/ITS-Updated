import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'

export const CONCEPTS = [
  'Variables', 'Functions', 'Loops', 'OOP',
  'Strings', 'Lists', 'Dictionaries', 'Error Handling',
]

export function useMastery() {
  const { token, user } = useAuth()
  const [mastery, setMastery] = useState([])
  const [loading, setLoading] = useState(true)
  const [overallMastery, setOverallMastery] = useState(0)

  const fetchMastery = useCallback(async () => {
    if (!token) return
    try {
      const { data } = await axios.get('/mastery', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setMastery(data)
    } catch {
      setMastery([])
    } finally {
      setLoading(false)
    }
  }, [token])

  // Curriculum-wide mastery, computed server-side across every concept
  // (unattempted concepts count as 0) -- see backend/app/api/mastery.py.
  const fetchOverallMastery = useCallback(async () => {
    if (!token) return
    try {
      const { data } = await axios.get('/mastery/overall', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setOverallMastery(Math.round((data.overall_mastery || 0) * 100))
    } catch {
      setOverallMastery(0)
    }
  }, [token])

  const refreshMastery = useCallback(async () => {
    await Promise.all([fetchMastery(), fetchOverallMastery()])
  }, [fetchMastery, fetchOverallMastery])

  useEffect(() => {
    refreshMastery()
  }, [refreshMastery])

  const getMasteryScore = useCallback((concept) => {
    const entry = mastery.find(m => m.concept === concept)
    return entry ? Math.round((entry.score || 0) * 100) : 0
  }, [mastery])

  const getWeakestConcept = useCallback(() => {
    if (!mastery.length) return 'Variables'
    return mastery.reduce((a, b) => (a.score < b.score ? a : b)).concept
  }, [mastery])

  return { mastery, loading, overallMastery, refreshMastery, getMasteryScore, getWeakestConcept }
}
