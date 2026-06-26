import './MasteryBar.css'

/**
 * MasteryBar — animated progress bar with color-coded mastery tiers.
 * Props:
 *   score   {number}  0.0 – 1.0
 *   label   {string}  concept name
 *   showPct {boolean} show percentage label (default true)
 */
export default function MasteryBar({ score = 0, label, showPct = true }) {
  const pct = Math.round(score * 100)

  const tier =
    pct >= 80 ? 'tier-master' :
    pct >= 60 ? 'tier-high'   :
    pct >= 33 ? 'tier-mid'    :
                'tier-low'

  return (
    <div className="mastery-bar-wrap">
      {label && (
        <div className="mastery-bar-header">
          <span className="mastery-bar-label">{label}</span>
          {showPct && (
            <span className={`mastery-bar-pct ${tier}`}>{pct}%</span>
          )}
        </div>
      )}
      <div className="mastery-bar-track">
        <div
          className={`mastery-bar-fill ${tier}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
