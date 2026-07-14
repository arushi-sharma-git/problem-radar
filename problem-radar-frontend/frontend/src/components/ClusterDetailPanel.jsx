import { useMemo, useState } from 'react'
import ConfidenceBadge from './ConfidenceBadge'
import IdeaCard from './IdeaCard'

const DIFFICULTIES = ['beginner', 'intermediate', 'advanced']

export default function ClusterDetailPanel({ cluster, insight, ideas, loading }) {
  const [difficultyFilter, setDifficultyFilter] = useState('All')

  const filteredIdeas = useMemo(() => {
    if (difficultyFilter === 'All') return ideas
    return ideas.filter((i) => i.difficulty === difficultyFilter)
  }, [ideas, difficultyFilter])

  if (loading) {
    return (
      <div className="loading-state">
        <div className="scan-line" />
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading cluster…
        </span>
      </div>
    )
  }

  if (!cluster || !insight) {
    return (
      <div className="empty-state">
        <div className="empty-state-title">No cluster selected</div>
        <p style={{ maxWidth: 360, fontSize: 13.5, lineHeight: 1.6 }}>
          Pick a cluster on the left to see its insight — the pain point,
          who it affects, and the project ideas generated against it.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="panel-header">
        <div>
          <h1 className="panel-title">{insight.domain}</h1>
          <div className="panel-tags">
            <span className="tag">{insight.article_ids.length} source articles</span>
          </div>
        </div>
        <div className="confidence-block">
          <span className="confidence-label">Confidence</span>
          <ConfidenceBadge confidence={insight.confidence} size="lg" />
        </div>
      </div>

      <div className="panel-section-label">Pain point</div>
      <p className="summary-text">{insight.pain_point}</p>

      <div className="panel-section-label">Affected group</div>
      <p className="summary-text">{insight.affected_group}</p>

      <div className="panel-section-label">Evidence gap</div>
      <p className="summary-text">{insight.evidence_gap}</p>

      <div className="ideas-header">
        <span className="panel-section-label" style={{ marginBottom: 0 }}>
          Project ideas ({filteredIdeas.length})
        </span>
        <div className="difficulty-filter">
          <button
            className={`difficulty-chip ${difficultyFilter === 'All' ? 'active' : ''}`}
            onClick={() => setDifficultyFilter('All')}
          >
            All
          </button>
          {DIFFICULTIES.map((d) => (
            <button
              key={d}
              className={`difficulty-chip ${d} ${difficultyFilter === d ? 'active' : ''}`}
              onClick={() => setDifficultyFilter(d)}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {filteredIdeas.length === 0 ? (
        <div className="empty-state" style={{ padding: '40px 10px' }}>
          <div className="empty-state-title">No ideas at this difficulty</div>
          <p style={{ fontSize: 13 }}>Try a different difficulty level.</p>
        </div>
      ) : (
        <div className="ideas-grid">
          {filteredIdeas.map((idea) => (
            <IdeaCard key={idea.id} idea={idea} />
          ))}
        </div>
      )}
    </div>
  )
}
