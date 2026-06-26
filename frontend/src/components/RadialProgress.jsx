/**
 * RadialProgress.jsx
 * Animated circular progress ring built with SVG + CSS.
 * Shows mastery percentage inside a glowing ring.
 */
import { useEffect, useRef } from 'react'
import './RadialProgress.css'

const LEVEL_COLOR = (pct) => {
  if (pct >= 80) return 'var(--green)'
  if (pct >= 50) return 'var(--cyan)'
  if (pct >= 25) return 'var(--indigo-light)'
  return 'var(--orange)'
}

export default function RadialProgress({
  score = 0,       // 0–1 float
  size = 80,       // px
  stroke = 6,      // stroke width
  label = '',      // text inside ring
  animate = true,
  showPct = true,
}) {
  const pct = Math.round(score * 100)
  const radius = (size - stroke * 2) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference
  const color = LEVEL_COLOR(pct)
  const circleRef = useRef(null)

  useEffect(() => {
    if (!animate || !circleRef.current) return
    const el = circleRef.current
    el.style.strokeDashoffset = circumference
    requestAnimationFrame(() => {
      el.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.34,1.56,0.64,1)'
      el.style.strokeDashoffset = offset
    })
  }, [pct, animate, circumference, offset])

  return (
    <div className="radial-progress" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--bg-surface-2)"
          strokeWidth={stroke}
        />
        {/* Progress */}
        <circle
          ref={circleRef}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={animate ? circumference : offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{
            filter: `drop-shadow(0 0 6px ${color}88)`,
          }}
        />
      </svg>
      <div className="radial-progress-label">
        {showPct && (
          <span className="radial-pct" style={{ color }}>{pct}%</span>
        )}
        {label && <span className="radial-name">{label}</span>}
      </div>
    </div>
  )
}
