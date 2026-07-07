import axios from 'axios'

const API_BASE = '/auth'

export async function apiLogin(username, password) {
  const { data } = await axios.post(`${API_BASE}/login`, { username, password })
  return data
}

export async function apiRegister(email, password, role = 'student') {
  const { data } = await axios.post(`${API_BASE}/register`, {
    email,
    password,
    role,
  })
  return data   // { message, email }
}

export async function apiVerifyOtp(email, otp) {
  const { data } = await axios.post(`${API_BASE}/verify-otp`, { email, otp })
  return data   // TokenResponse
}

export async function apiResendOtp(email) {
  const { data } = await axios.post(`${API_BASE}/resend-otp`, { email })
  return data   // { message, email }
}

export async function apiMe(token) {
  const { data } = await axios.get(`${API_BASE}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return data
}

export async function apiLogout(token) {
  await axios.post(`${API_BASE}/logout`, {}, {
    headers: { Authorization: `Bearer ${token}` },
  })
}
