/**
 * MessageBubble — renders a single chat message.
 * User messages: right-aligned, indigo gradient.
 * Assistant messages: left-aligned, surface card with robot avatar.
 *
 * Props:
 *   role      'user' | 'assistant'
 *   content   string  (supports ```code``` blocks)
 *   concept   string | null
 *   timestamp string | null
 */
export default function MessageBubble({ role, content, concept, timestamp }) {
  const isUser = role === 'user'

  /** Simple inline markdown-ish renderer: ```code``` → <pre><code> */
  const renderContent = (text) => {
    const parts = text.split(/(```[\s\S]*?```)/g)
    return parts.map((part, i) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3).replace(/^python\n?/, '')
        return (
          <pre key={i} className="msg-code-block">
            <code>{code}</code>
          </pre>
        )
      }
      // Inline bold **text**
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g)
      return (
        <span key={i}>
          {boldParts.map((bp, j) =>
            bp.startsWith('**') && bp.endsWith('**')
              ? <strong key={j}>{bp.slice(2, -2)}</strong>
              : <span key={j}>{bp}</span>
          )}
        </span>
      )
    })
  }

  return (
    <div className={`msg-row ${isUser ? 'msg-row-user' : 'msg-row-assistant'} animate-fade-in`}>
      {!isUser && (
        <div className="msg-avatar msg-avatar-bot" aria-hidden="true">🤖</div>
      )}

      <div className={`msg-bubble ${isUser ? 'msg-bubble-user' : 'msg-bubble-assistant'}`}>
        {concept && !isUser && (
          <div className="msg-concept-tag">📌 {concept}</div>
        )}
        <div className="msg-content">{renderContent(content)}</div>
        {timestamp && (
          <div className="msg-timestamp">
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>

      {isUser && (
        <div className="msg-avatar msg-avatar-user" aria-hidden="true">👤</div>
      )}
    </div>
  )
}
