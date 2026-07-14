import ConfidenceBadge from './ConfidenceBadge'

export default function ClusterCard({ cluster, active, onSelect }) {
  return (
    <button
      className={`signal-card ${active ? 'active' : ''}`}
      onClick={() => onSelect(cluster.cluster_id)}
      aria-pressed={active}
    >
      <div className="signal-card-top">
        <span className="signal-card-title">{cluster.domain}</span>
      </div>
      <div className="signal-card-meta">
        <ConfidenceBadge confidence={cluster.confidence} />
        <span className="mentions">{cluster.article_count} articles</span>
      </div>
    </button>
  )
}
