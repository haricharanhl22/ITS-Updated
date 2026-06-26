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

  useEffect(() => {
    fetchMastery()
  }, [fetchMastery])

  const getMasteryScore = useCallback((concept) => {
    const entry = mastery.find(m => m.concept === concept)
    return entry ? Math.round((entry.score || 0) * 100) : 0
  }, [mastery])

  const getWeakestConcept = useCallback(() => {
    if (!mastery.length) return 'Variables'
    return mastery.reduce((a, b) => (a.score < b.score ? a : b)).concept
  }, [mastery])

  return { mastery, loading, refreshMastery: fetchMastery, getMasteryScore, getWeakestConcept }
}
