/**
 * TypewriterText.jsx
 * Renders text character-by-character with a blinking cursor.
 * Used for bot responses in the chat page.
 */
import { useEffect, useRef, useState } from 'react'
import './TypewriterText.css'

export default function TypewriterText({ text = '', speed = 12, onDone }) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone]           = useState(false)
  const indexRef = useRef(0)
  const timerRef = useRef(null)

  useEffect(() => {
    // Reset on new text
    indexRef.current = 0
    setDisplayed('')
    setDone(false)

    const tick = () => {
      if (indexRef.current < text.length) {
        const slice = text.slice(0, indexRef.current + 1)
        setDisplayed(slice)
        indexRef.current++

        // Variable speed: pause a bit longer after punctuation
        const ch = text[indexRef.current - 1]
        const delay = (ch === '.' || ch === '!' || ch === '?') ? speed * 8 :
                      (ch === ',')                              ? speed * 3 : speed
        timerRef.current = setTimeout(tick, delay)
      } else {
        setDone(true)
        onDone?.()
      }
    }

    timerRef.current = setTimeout(tick, speed)
    return () => clearTimeout(timerRef.current)
  }, [text]) // eslint-disable-line react-hooks/exhaustive-deps

  // Render markdown-like formatting (bold, code, newlines)
  const renderText = (t) => {
    const parts = t.split(/(`[^`]*`|\*\*[^*]+\*\*|\n)/g)
    return parts.map((part, i) => {
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="tw-code">{part.slice(1, -1)}</code>
      }
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>
      }
      if (part === '\n') return <br key={i} />
      return part
    })
  }

  return (
    <span className="typewriter">
      {renderText(displayed)}
      {!done && <span className="tw-cursor" aria-hidden />}
    </span>
  )
}
