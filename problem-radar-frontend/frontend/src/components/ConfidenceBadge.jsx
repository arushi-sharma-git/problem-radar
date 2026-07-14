const LABEL = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
}

export default function ConfidenceBadge({ confidence, size = 'sm' }) {
  return (
    <span className={`confidence-badge ${confidence} ${size === 'lg' ? 'lg' : ''}`}>
      <span className="confidence-dot" />
      {LABEL[confidence] ?? confidence}
    </span>
  )
}
