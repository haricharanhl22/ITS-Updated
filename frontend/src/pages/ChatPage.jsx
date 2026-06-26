import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useMastery } from '../hooks/useMastery'
import TypewriterText from '../components/TypewriterText'
import SourcesChip from '../components/SourcesChip'
import RadialProgress from '../components/RadialProgress'
import axios from 'axios'
import './ChatPage.css'

const STARTER_QUESTIONS = [
  'What is a lambda function?',
  'How do for loops work?',
  'Explain OOP in Python',
  'How do I use f-strings?',
]

const CONCEPT_EMOJI = {
  'Variables': '📦', 'Functions': '⚙️', 'Loops': '🔁',
  'OOP': '🏗️', 'Strings': '🔤', 'Lists': '📋',
  'Dictionaries': '📖', 'Error Handling': '⚠️',
}

const FOLLOW_UPS = {
  'Variables': ['How do I name a variable?', 'What is variable typing?', 'Give me a variables practice code'],
  'Functions': ['Explain return values', 'How do I pass arguments?', 'Can a function return multiple values?'],
  'Loops': ['What is a while loop?', 'Explain break and continue keywords', 'How do I use range() in loops?'],
  'OOP': ['What is a class constructor?', 'Explain self parameter', 'Give me a simple class example'],
  'Strings': ['How do I split a string?', 'What are string methods?', 'Explain string formatting (f-strings)'],
  'Lists': ['How do I append to a list?', 'Explain list indexing/slicing', 'How do I loop through a list?'],
  'Dictionaries': ['How do I access a dictionary value?', 'Explain key-value pairs', 'How do I iterate over dictionaries?'],
  'Error Handling': ['What is try-except?', 'How do I handle multiple exceptions?', 'Explain finally block']
}

export default function ChatPage() {
  const { token, user } = useAuth()
  const { mastery, refreshMastery } = useMastery()
  const navigate = useNavigate()

  const [messages,      setMessages]      = useState([])
  const [activeConcept, setActiveConcept] = useState(null)
  const [activeScore,   setActiveScore]   = useState(0)
  const [input,         setInput]         = useState('')
  const [sending,       setSending]       = useState(false)
  const [chatError,     setChatError]     = useState(null)
  const [isTyping,      setIsTyping]      = useState(false)
  const [typingDone,    setTypingDone]    = useState({})  // msgId → bool
  const [copiedId,      setCopiedId]      = useState(null)

  const messagesEndRef = useRef(null)
  const textareaRef    = useRef(null)

  // Load message history on mount
  useEffect(() => {
    if (!user?.id || !token) return
    axios.get('/chat/messages', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setMessages(r.data.map(m => ({ ...m, isNew: false }))))
      .catch(() => {})
  }, [user?.id, token])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  // Sync active concept mastery score
  useEffect(() => {
    if (!activeConcept) return
    const entry = mastery.find(m => m.concept === activeConcept)
    setActiveScore(entry ? Math.round((entry.score || 0) * 100) : 0)
  }, [activeConcept, mastery])

  const handleInputChange = (e) => {
    setInput(e.target.value)
    const ta = textareaRef.current
    if (ta) { ta.style.height = 'auto'; ta.style.height = `${Math.min(ta.scrollHeight, 140)}px` }
  }

  const sendMessage = async (text) => {
    const question = (text || input).trim()
    if (!question || sending) return

    setInput('')
    setSending(true)
    setChatError(null)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const userMsg = { id: Date.now(), role: 'user', content: question, isNew: true }
    setMessages(prev => [...prev, userMsg])
    setIsTyping(true)

    // Update LocalStorage stats (XP, active dates, daily goals)
    try {
      const totalAsked = parseInt(localStorage.getItem('hcai_questions_asked') || '0', 10) + 1
      localStorage.setItem('hcai_questions_asked', totalAsked.toString())

      const todayStr = new Date().toDateString()
      const askedToday = parseInt(localStorage.getItem(`hcai_questions_today_${todayStr}`) || '0', 10) + 1
      localStorage.setItem(`hcai_questions_today_${todayStr}`, askedToday.toString())

      const chatLog = JSON.parse(localStorage.getItem('hcai_chat_activity_log') || '[]')
      if (!chatLog.includes(todayStr)) {
        chatLog.push(todayStr)
        localStorage.setItem('hcai_chat_activity_log', JSON.stringify(chatLog))
      }
    } catch (e) {}

    try {
      const { data } = await axios.post('/api/ask', {
        question,
      }, { headers: { Authorization: `Bearer ${token}` } })

      setIsTyping(false)
      setActiveConcept(data.concept || null)

      const botId = Date.now() + 1
      const botMsg = {
        id: botId,
        role: 'assistant',
        content: data.response,
        concept: data.concept,
        cited_chunks: data.cited_chunks || [],
        mastery_before: data.mastery_before,
        isNew: true,
      }
      setMessages(prev => [...prev, botMsg])
      setTypingDone(prev => ({ ...prev, [botId]: false }))

      // Refresh mastery sidebar after chat
      refreshMastery()
    } catch (err) {
      setIsTyping(false)
      const detail = err?.response?.data?.detail
      setChatError(typeof detail === 'string' ? detail : err.message || 'Failed to reach tutor')
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  // Parse inline and block code + Copy Button with 1.5s visual feedback
  const renderMessageContent = (text, msgId) => {
    const parts = text.split(/(```[\s\S]*?```)/g)
    return parts.map((part, i) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const lines = part.split('\n')
        const firstLine = lines[0].slice(3).trim()
        const lang = firstLine || 'python'
        const code = lines.slice(1, -1).join('\n')
        
        const blockKey = `${msgId}-${i}`
        const isCopied = copiedId === blockKey
        
        return (
          <div key={i} className="code-block-container" style={{ position: 'relative', margin: '12px 0', borderRadius: '8px', overflow: 'hidden', border: isCopied ? '1.5px solid var(--green)' : '1px solid var(--border)' }}>
            <div className="code-block-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface-2)', padding: '6px 12px', fontSize: '0.75rem', borderBottom: '1px solid var(--border)' }}>
              <span style={{ color: 'var(--text-muted)' }}>{lang}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(code)
                  setCopiedId(blockKey)
                  setTimeout(() => setCopiedId(null), 1500)
                }}
                style={{
                  background: 'transparent',
                  border: isCopied ? '1px solid var(--green)' : '1px solid var(--border)',
                  color: isCopied ? 'var(--green)' : 'var(--text-muted)',
                  borderRadius: '4px',
                  padding: '2px 8px',
                  cursor: 'pointer',
                  fontSize: '0.7rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.15s ease'
                }}
              >
                {isCopied ? '✓ Copied' : '📄 Copy'}
              </button>
            </div>
            <pre className="msg-code-block" style={{ margin: 0, padding: '12px', overflowX: 'auto', background: 'hsl(222, 20%, 10%)' }}>
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: '#f8f8f2' }}>{code}</code>
            </pre>
          </div>
        )
      }
      
      const inlineParts = part.split(/(`[^`]*`|\*\*[^*]+\*\*)/g)
      return (
        <span key={i}>
          {inlineParts.map((bp, j) => {
            if (bp.startsWith('`') && bp.endsWith('`')) {
              return <code key={j} className="tw-code" style={{ background: 'var(--bg-surface-2)', padding: '2px 6px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{bp.slice(1, -1)}</code>
            }
            if (bp.startsWith('**') && bp.endsWith('**')) {
              return <strong key={j}>{bp.slice(2, -2)}</strong>
            }
            return bp
          })}
        </span>
      )
    })
  }

  // Detect if follow ups should render
  const lastMsg = messages[messages.length - 1]
  const showFollowUps = lastMsg && lastMsg.role === 'assistant' && (typingDone[lastMsg.id] !== false)
  const currentFollowUps = activeConcept ? (FOLLOW_UPS[activeConcept] || STARTER_QUESTIONS) : STARTER_QUESTIONS

  return (
    <div className="chat-page">
      {/* ── Sidebar ── */}
      <aside className="chat-sidebar">
        <div className="chat-sidebar-header">
          <button className="chat-sidebar-back" onClick={() => navigate('/dashboard')} title="Dashboard">
            ← Dashboard
          </button>
        </div>

        <div className="chat-sidebar-persona">
          <div className="chat-persona-emoji">👤</div>
          <div>
            <div className="chat-persona-name">{user?.email?.split('@')[0] || 'Learner'}</div>
            <div className="chat-persona-level">Student</div>
          </div>
        </div>

        {activeConcept && (
          <div className="chat-active-concept">
            <div className="chat-concept-label">Active Concept</div>
            <div className="chat-concept-ring">
              <RadialProgress score={activeScore / 100} size={68} stroke={5} showPct />
              <span className="chat-concept-name">
                {CONCEPT_EMOJI[activeConcept]} {activeConcept}
              </span>
            </div>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => navigate(`/quiz/${encodeURIComponent(activeConcept)}`)}
              id="btn-quiz-from-chat"
            >
              Take Quiz →
            </button>
          </div>
        )}

        <div className="chat-sidebar-mastery">
          <div className="chat-mastery-title">Mastery</div>
          {mastery.slice(0, 5).map(m => (
            <div key={m.concept} className="chat-mastery-row">
              <span className="chat-mastery-concept">{CONCEPT_EMOJI[m.concept] || '📝'} {m.concept}</span>
              <div className="chat-mastery-bar-wrap">
                <div className="chat-mastery-bar-fill" style={{
                  width: `${Math.round((m.score || 0) * 100)}%`,
                  background: m.score >= 0.8 ? 'var(--green)' : m.score >= 0.5 ? 'var(--cyan)' : 'var(--indigo-light)',
                }} />
              </div>
              <span className="chat-mastery-pct">{Math.round((m.score || 0) * 100)}%</span>
            </div>
          ))}
        </div>

        <button className="chat-sidebar-logout" onClick={() => navigate('/logout')}>
          Sign Out
        </button>
      </aside>

      {/* ── Chat main ── */}
      <div className="chat-main">
        <div className="chat-topbar">
          <span className="chat-topbar-title">🤖 AI Python Tutor</span>
          {activeConcept && (
            <span className="chat-topbar-concept">
              {CONCEPT_EMOJI[activeConcept]} {activeConcept}
              <span className="chat-topbar-score">{activeScore}%</span>
            </span>
          )}
          <div style={{ flex: 1 }} />
          <span className="chat-topbar-hint" style={{ color: 'var(--indigo-light)', fontSize: '0.78rem' }}>
            ✨ AI Powered by Groq
          </span>
        </div>

        <div className="chat-messages" role="log" aria-live="polite">
          {messages.length === 0 && !isTyping ? (
            <div className="chat-welcome">
              <div className="chat-welcome-icon">🤖</div>
              <h1 className="chat-welcome-title">Hi {user?.email?.split('@')[0] || 'Learner'}, ready to learn?</h1>
              <p className="chat-welcome-sub">Ask me anything about Python — variables, functions, loops, OOP, and more.</p>
              <div className="chat-welcome-chips">
                {STARTER_QUESTIONS.map((q, idx) => (
                  <button
                    key={q}
                    className="chat-chip"
                    onClick={() => sendMessage(q)}
                    id={`starter-${q.slice(0,10).replace(/\s+/g,'-').toLowerCase()}`}
                    style={{ animationDelay: `${idx * 50}ms` }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map(msg => (
                <div key={msg.id} className={`msg-row ${msg.role === 'user' ? 'msg-row-user' : 'msg-row-bot'}`}>
                  {msg.role === 'assistant' && (
                    <div className="msg-avatar msg-avatar-bot">🤖</div>
                  )}
                  <div className={`msg-bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-bot'}`}>
                    {msg.role === 'assistant' && msg.isNew && typingDone[msg.id] === false ? (
                      <TypewriterText
                        text={msg.content}
                        speed={10}
                        onDone={() => setTypingDone(prev => ({ ...prev, [msg.id]: true }))}
                      />
                    ) : (
                      <span className="bubble-text">{renderMessageContent(msg.content, msg.id)}</span>
                    )}
                    {msg.role === 'assistant' && msg.cited_chunks?.length > 0 && (
                      <SourcesChip chunks={msg.cited_chunks} />
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="msg-avatar msg-avatar-user">👤</div>
                  )}
                </div>
              ))}

              {isTyping && (
                <div className="msg-row msg-row-bot animate-fade-in">
                  <div className="msg-avatar msg-avatar-bot">🤖</div>
                  <div className="typing-bubble">
                    <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                  </div>
                </div>
              )}

              {chatError && (
                <div className="chat-error-bubble animate-fade-in" role="alert">
                  <span>⚠️</span> {chatError}
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input & Follow-ups */}
        <div className="chat-input-area-container" style={{ position: 'relative' }}>
          
          {/* Staggered Follow-up suggestions */}
          {showFollowUps && (
            <div className="chat-followups-bar animate-fade-in" style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', padding: '8px 20px', background: 'transparent', justifyContent: 'center' }}>
              {currentFollowUps.map((q, idx) => (
                <button
                  key={q}
                  className="chat-followup-chip"
                  onClick={() => sendMessage(q)}
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          <div className="chat-input-area">
            <div className="chat-input-wrap">
              <textarea
                ref={textareaRef}
                id="chat-input"
                className="chat-input"
                placeholder="Ask a Python question… (Enter to send)"
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={sending}
                aria-label="Type your question"
              />
              <button
                id="btn-send-chat"
                className="chat-send-btn"
                onClick={() => sendMessage()}
                disabled={!input.trim() || sending}
                aria-label="Send message"
              >
                {sending ? <span className="spinner" style={{ width: 16, height: 16 }} /> : '↑'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
