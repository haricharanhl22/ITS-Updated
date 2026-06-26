/**
 * api/tutor.js — Frontend API helpers for the HCAI-ITS tutoring system
 */
import axios from 'axios'

/**
 * POST /api/ask — RAG-powered chat
 * Returns { response, concept, mastery_before, cited_chunks }
 */
export async function apiAsk(studentId, question, token) {
  const { data } = await axios.post(
    '/api/ask',
    { student_id: String(studentId), question },
    { headers: { Authorization: `Bearer ${token}` } },
  )
  return data
}

/**
 * GET /chat/messages/{studentId} — load chat history
 */
export async function apiGetMessages(studentId, token) {
  const { data } = await axios.get(`/chat/messages/${studentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return data
}

/**
 * GET /assessments/{concept} — fetch quiz questions
 */
export async function apiGetAssessment(concept, token) {
  const { data } = await axios.get(`/assessments/${encodeURIComponent(concept)}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return data
}

/**
 * POST /assessments/submit — submit quiz answers
 * Returns { score, correct_count, total, new_mastery, mastery_delta }
 */
export async function apiSubmitQuiz(studentId, concept, answers, token) {
  const { data } = await axios.post(
    '/assessments/submit',
    { student_id: String(studentId), concept, answers },
    { headers: { Authorization: `Bearer ${token}` } },
  )
  return data
}

/**
 * GET /api/learning-events/{studentId} — mastery history for sparklines
 */
export async function apiGetLearningEvents(studentId, token, limit = 50) {
  const { data } = await axios.get(`/api/learning-events/${studentId}`, {
    params: { limit },
    headers: { Authorization: `Bearer ${token}` },
  })
  return data
}

/**
 * GET /mastery/{studentId} — all concept mastery scores
 */
export async function apiGetMastery(studentId, token) {
  const { data } = await axios.get(`/mastery/${studentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return data
}

/**
 * POST /demo/login — get JWT for a demo persona
 */
export async function apiDemoLogin(persona) {
  const { data } = await axios.post('/demo/login', { persona })
  return data
}
