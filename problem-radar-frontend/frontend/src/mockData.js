// Mirrors the exact response shapes from api.py:
//   GET /clusters               -> ClusterSummary[]
//   GET /clusters/{id}/insight  -> InsightOut
//   GET /clusters/{id}/ideas    -> IdeaOut[]

export const MOCK_CLUSTERS = [
  { cluster_id: 1, domain: 'Freelance & Consulting', confidence: 'high', article_count: 18 },
  { cluster_id: 2, domain: 'Healthcare Ops', confidence: 'high', article_count: 12 },
  { cluster_id: 3, domain: 'Creator Tools', confidence: 'medium', article_count: 9 },
  { cluster_id: 4, domain: 'Property Management', confidence: 'medium', article_count: 14 },
  { cluster_id: 5, domain: 'Gaming / Indie Dev', confidence: 'low', article_count: 5 },
]

export const MOCK_INSIGHTS = {
  1: {
    id: 101,
    cluster_id: 1,
    domain: 'Freelance & Consulting',
    pain_point:
      "Freelancers repeatedly describe losing money because small extra client asks pile up over email and Slack, and nobody logs them against the original quote.",
    affected_group: 'Independent freelancers and small consultancies working on fixed-quote projects',
    evidence_gap:
      'Existing time-tracking tools (Harvest, Toggl) log hours but have no concept of "scope" vs "quote", so nothing flags drift automatically.',
    confidence: 'high',
    article_ids: [1, 4, 9, 15, 22],
  },
  2: {
    id: 102,
    cluster_id: 2,
    domain: 'Healthcare Ops',
    pain_point:
      'Independent clinic admins describe 15-20% no-show rates and say scheduling software has no risk-scoring for which patients are likely to skip.',
    affected_group: 'Administrators at small independent clinics (1-5 providers)',
    evidence_gap:
      'Mainstream scheduling tools optimize for booking convenience, not attendance prediction, leaving a gap for a lightweight risk-scoring layer.',
    confidence: 'high',
    article_ids: [3, 7, 11],
  },
  3: {
    id: 103,
    cluster_id: 3,
    domain: 'Creator Tools',
    pain_point:
      'Writers post the same essay to Substack, LinkedIn, Medium and X, and manually strip/re-add formatting each time.',
    affected_group: 'Independent newsletter and long-form content writers',
    evidence_gap: 'Cross-posting tools handle scheduling but not long-form reflow between platforms.',
    confidence: 'medium',
    article_ids: [2, 8],
  },
  4: {
    id: 104,
    cluster_id: 4,
    domain: 'Property Management',
    pain_point:
      'Landlords with 2-10 units default to text threads and paper receipts for maintenance history since enterprise tools are overkill and expensive.',
    affected_group: 'Small-scale landlords managing under 10 units without a management company',
    evidence_gap: 'Existing property management suites assume portfolios of 50+ units and price accordingly.',
    confidence: 'medium',
    article_ids: [5, 6, 13],
  },
  5: {
    id: 105,
    cluster_id: 5,
    domain: 'Gaming / Indie Dev',
    pain_point:
      'Indie developers mention paying agencies for store-page and patch-note translation, with slow turnaround for frequent updates.',
    affected_group: 'Solo and small-team indie game developers publishing on Steam',
    evidence_gap: 'Signal volume is still thin here — worth re-scanning before committing to this one.',
    confidence: 'low',
    article_ids: [10],
  },
}

export const MOCK_IDEAS = {
  1: [
    {
      id: 1,
      problem_statement: 'Freelancers have no automated way to flag out-of-scope client requests before doing the work.',
      target_user: 'Freelance designers, developers, and consultants on fixed-quote contracts',
      suggested_approach:
        'Build a Gmail/Slack watcher that parses inbound client messages, compares against the stored quote, and drafts a "this is extra" reply with a price delta.',
      tech_angle: 'Gmail API + Slack API for ingestion, an LLM classifier for scope-drift detection',
      difficulty: 'intermediate',
      feasibility_score: 4,
      impact_score: 4,
    },
    {
      id: 2,
      problem_statement: 'Freelancers want a simple way to tag messages as "in scope" vs "extra" without a full CRM.',
      target_user: 'Solo freelancers who find full CRMs like HoneyBook too heavy',
      suggested_approach: 'A browser extension that adds tag buttons to Gmail/Slack threads and tallies scope delta automatically.',
      tech_angle: 'Chrome extension + lightweight local storage, no backend required for v1',
      difficulty: 'beginner',
      feasibility_score: 5,
      impact_score: 3,
    },
  ],
  2: [
    {
      id: 3,
      problem_statement: 'Clinics need a way to predict which upcoming appointments are likely no-shows.',
      target_user: 'Front-desk admins at independent clinics',
      suggested_approach:
        'Train a simple risk model on a clinic\'s historical booking data (day/time, lead time, patient history) and surface a risk score in the existing calendar view.',
      tech_angle: 'Scikit-learn logistic regression to start; calendar plug-in via CalDAV or a common EHR API',
      difficulty: 'advanced',
      feasibility_score: 2,
      impact_score: 5,
    },
  ],
  3: [
    {
      id: 4,
      problem_statement: 'Writers need one draft to auto-reformat correctly for four different platforms.',
      target_user: 'Newsletter writers cross-posting to Substack, LinkedIn, Medium, and X',
      suggested_approach: 'Parse a single markdown draft and emit platform-correct formatting, header sizing, and link handling per target.',
      tech_angle: 'Markdown AST parsing + per-platform formatting rules, no ML needed',
      difficulty: 'beginner',
      feasibility_score: 5,
      impact_score: 3,
    },
  ],
  4: [
    {
      id: 5,
      problem_statement: 'Micro-landlords have no lightweight, zero-onboarding way to log maintenance history.',
      target_user: 'Landlords managing 2-10 units without a property manager',
      suggested_approach: 'Tenants text a photo and description; the system builds a dated, searchable maintenance record automatically.',
      tech_angle: 'Twilio SMS webhook + simple relational store, no app install required for tenants',
      difficulty: 'intermediate',
      feasibility_score: 4,
      impact_score: 3,
    },
  ],
  5: [
    {
      id: 6,
      problem_statement: 'Indie devs need affordable, fast localization for frequently-changing patch notes.',
      target_user: 'Solo indie developers publishing on Steam',
      suggested_approach: 'A translation queue with a persistent glossary of game-specific terms to keep translations consistent across updates.',
      tech_angle: 'Translation API + a glossary/term-memory layer on top',
      difficulty: 'intermediate',
      feasibility_score: 3,
      impact_score: 2,
    },
  ],
}
