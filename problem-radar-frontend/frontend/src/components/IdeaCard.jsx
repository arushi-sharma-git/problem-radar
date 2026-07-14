import SignalMeter from './SignalMeter'

const DIFFICULTY_LABEL = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
}

export default function IdeaCard({ idea }) {
  return (
    <div className="idea-card">
      <div className="idea-card-top">
        <div className="idea-card-title">{idea.problem_statement}</div>
        <span className={`effort-badge ${idea.difficulty}`}>
          {DIFFICULTY_LABEL[idea.difficulty] ?? idea.difficulty}
        </span>
      </div>

      <div className="idea-card-field">
        <span className="idea-card-field-label">Target user</span>
        <span className="idea-card-field-value">{idea.target_user}</span>
      </div>
      <div className="idea-card-field">
        <span className="idea-card-field-label">Suggested approach</span>
        <span className="idea-card-field-value">{idea.suggested_approach}</span>
      </div>
      <div className="idea-card-field">
        <span className="idea-card-field-label">Tech angle</span>
        <span className="idea-card-field-value">{idea.tech_angle}</span>
      </div>

      <div className="idea-card-scores">
        <SignalMeter value={idea.feasibility_score} max={5} label="Feasibility" />
        <SignalMeter value={idea.impact_score} max={5} label="Impact" />
      </div>
    </div>
  )
}
