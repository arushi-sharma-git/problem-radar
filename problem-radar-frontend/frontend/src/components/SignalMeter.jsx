const BAR_COUNT = 12

function colorFor(ratio) {
  if (ratio >= 0.75) return 'var(--amber)'
  if (ratio >= 0.5) return 'var(--teal)'
  return 'var(--text-low)'
}

// Renders a score as a segmented signal-strength readout (like a scanner
// bar) instead of a plain number or badge. `max` lets it represent both
// the 0-5 feasibility/impact scores and any future 0-100 scores.
export default function SignalMeter({ value, max = 100, size = 'sm', label }) {
  const ratio = Math.max(0, Math.min(1, value / max))
  const litCount = Math.round(ratio * BAR_COUNT)
  const color = colorFor(ratio)
  const displayValue = max === 100 ? `${value}%` : `${value}/${max}`

  return (
    <div className={`signal-meter ${size === 'lg' ? 'lg' : ''}`}>
      {label && <span className="signal-meter-label">{label}</span>}
      <div className="signal-meter-bars" style={{ '--meter-color': color }}>
        {Array.from({ length: BAR_COUNT }).map((_, i) => {
          const heightPct = 30 + (i / BAR_COUNT) * 70
          return (
            <div
              key={i}
              className={`signal-meter-bar ${i < litCount ? 'lit' : ''}`}
              style={{ height: `${heightPct}%` }}
            />
          )
        })}
      </div>
      <span className="signal-meter-value">{displayValue}</span>
    </div>
  )
}
