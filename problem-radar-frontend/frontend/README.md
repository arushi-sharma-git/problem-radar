# Problem Radar — Frontend

A console-style UI for browsing your `api.py` FastAPI backend: clusters of
real-world problems, the extracted insight for each, and the generated
student project ideas.

## Stack
- React 18 + Vite
- No UI framework — a hand-rolled design system in `src/index.css`
- Talks directly to your FastAPI backend (matches `api.py` exactly — see
  below), and falls back to bundled mock data if that backend isn't running

## Run it

```bash
cd frontend
npm install
npm run dev
```

Opens on `http://localhost:5173`. In another terminal, run your backend as
usual:

```bash
uvicorn api:app --reload
```

The frontend calls `http://127.0.0.1:8000` directly by default (see
`.env.example` — copy it to `.env.local` to change it). `api.py` already
sets `allow_origins=["*"]`, so no dev-server proxy is needed.

## Endpoints this frontend calls

Matches `api.py` one-to-one:

| Method | Path                          | Used for                          |
|--------|-------------------------------|------------------------------------|
| GET    | `/clusters`                   | Sidebar list (`ClusterSummary[]`)  |
| GET    | `/clusters/{cluster_id}/insight` | Detail panel (`InsightOut`)     |
| GET    | `/clusters/{cluster_id}/ideas`   | Detail panel (`IdeaOut[]`)      |
| GET    | `/ideas?difficulty=&domain=`  | Exposed in `api.js` (`fetchAllIdeas`) but not wired into the UI yet — a natural next screen |

If the backend isn't running, the UI automatically falls back to
`src/mockData.js`, which mirrors the exact shape of `ClusterSummary`,
`InsightOut`, and `IdeaOut` from `api.py`. Set `VITE_USE_MOCKS=true` in
`.env.local` to force mock mode even with the backend running.

## Project structure

```
src/
  api.js                        fetch helpers matching api.py, mock fallback
  mockData.js                    sample clusters/insights/ideas, same shape as api.py's responses
  index.css                      design system (tokens, layout, components)
  App.jsx                        shell: topbar, domain filter, cluster list, detail panel
  components/
    ConfidenceBadge.jsx           renders the high/medium/low confidence field
    SignalMeter.jsx                segmented readout, used for feasibility_score / impact_score (out of 5)
    ClusterCard.jsx                 sidebar list item (domain, confidence, article_count)
    DomainFilter.jsx                 pill-chip filter bar, grouped by real `domain` values
    IdeaCard.jsx                      one project idea (problem_statement, target_user, suggested_approach, tech_angle, difficulty, scores)
    ClusterDetailPanel.jsx            right-hand view: insight fields + idea cards, with a difficulty filter
```

## Notes on the data model

- `confidence` is categorical (`"high" | "medium" | "low"`) on both
  `ClusterSummary` and `InsightOut` — rendered as a colored badge, not a
  percentage meter.
- `feasibility_score` / `impact_score` are integers 0-5 on each idea —
  rendered as two small segmented meters (`SignalMeter` with `max={5}`).
- `difficulty` is `"beginner" | "intermediate" | "advanced"` — rendered as a
  badge on each idea card, and as a client-side filter in the detail panel
  (mirrors the `<select>` in your original `frontend.html`).

## Deploying to your repo

```bash
git add frontend
git commit -m "Add React frontend for api.py"
git push
```
