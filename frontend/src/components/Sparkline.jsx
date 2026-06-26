/**
 * Sparkline.jsx
 * Tiny SVG line chart showing mastery over time for a concept.
 */
export default function Sparkline({ data = [], width = 80, height = 28, color = 'var(--indigo-light)' }) {
  if (!data || data.length < 2) {
    return (
      <svg width={width} height={height}>
        <line x1={0} y1={height / 2} x2={width} y2={height / 2}
          stroke="var(--bg-surface-2)" strokeWidth={1.5} strokeDasharray="3 3" />
      </svg>
    )
  }

  const max = Math.max(...data, 1)
  const min = Math.min(...data, 0)
  const range = max - min || 1
  const pad = 3

  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (width - pad * 2)
    const y = pad + (1 - (v - min) / range) * (height - pad * 2)
    return [x, y]
  })

  const polyline = points.map(([x, y]) => `${x},${y}`).join(' ')

  // Area fill
  const areaPoints = [
    `${points[0][0]},${height}`,
    ...points.map(([x, y]) => `${x},${y}`),
    `${points[points.length - 1][0]},${height}`,
  ].join(' ')

  return (
    <svg width={width} height={height} overflow="visible">
      <defs>
        <linearGradient id={`sg-${color.replace(/[^a-z]/gi, '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon
        points={areaPoints}
        fill={`url(#sg-${color.replace(/[^a-z]/gi, '')})`}
      />
      <polyline
        points={polyline}
        fill="none"
        stroke={color}
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Last data point dot */}
      <circle
        cx={points[points.length - 1][0]}
        cy={points[points.length - 1][1]}
        r={2.5}
        fill={color}
      />
    </svg>
  )
}
