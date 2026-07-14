# problem-radar

An AI pipeline that scrapes news and blogs across 13 domains, discovers real-world problems worth solving, and turns them into concrete, scoped project ideas — grounded in real, current articles instead of generic brainstorming.

**Live pipeline:** scrape → embed → dedupe → cluster into themes → extract a structured insight per theme → generate project ideas → serve it all through an API and a browsable UI.

---

## Why this exists

Most "find a project idea" advice is generic or stale. problem-radar instead:

1. Continuously ingests real articles across science, climate, technology, health, urban planning, design, finance, society, and more — not just tech/AI news.
2. Groups them into emergent themes using embedding similarity, not a fixed keyword taxonomy.
3. Asks an LLM to extract the actual recurring pain point behind each theme, grounded only in what the articles say — and to say so honestly when a theme doesn't cleanly resolve to one problem, rather than forcing an answer.
4. Generates 2-3 concrete project ideas per theme, varying in difficulty, deliberately not defaulting to an AI/ML solution unless the problem genuinely calls for one.

## Architecture

```
RSS feeds (33 sources, 13 domains)
        │  feedparser + trafilatura
        ▼
  Scrape & clean article text
        │  sentence-transformers (all-MiniLM-L6-v2, local, free)
        ▼
  Embed (384-dim vectors)
        │  pgvector cosine-distance dedup
        ▼
  Store in Postgres (articles table)
        │  scheduled every 30 min via Celery Beat + Redis
        ▼
  ─────────────────────────────────────
  UMAP (dimensionality reduction)
        ▼
  HDBSCAN (density-based clustering)
        │  Gemini: name each cluster's theme/domain
        ▼
  Clusters of thematically-related articles
        ▼
  Gemini: extract a structured insight per cluster
  (pain point, affected group, evidence gap, confidence)
        │  pydantic-validated JSON, cached by cluster + prompt version
        ▼
  Gemini: generate 2-3 project ideas per insight
  (varying difficulty, not AI-biased)
        │  pydantic-validated JSON
        ▼
  Postgres (insights, ideas tables)
        ▼
  FastAPI (REST endpoints, Swagger docs at /docs)
        ▼
  React frontend (browsable UI, falls back to mock data if the API is offline)
```

## Stack

| Layer | Technology |
|---|---|
| Ingestion | Python, `feedparser`, `trafilatura` |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim, fully local) |
| Storage | PostgreSQL + `pgvector` (Docker) |
| Scheduling | Celery + Redis (Docker), 30-minute ingestion cycle |
| Clustering | UMAP (dimensionality reduction) + HDBSCAN (no need to pre-specify cluster count) |
| LLM | Gemini API (`gemini-3.1-flash-lite`) — cluster tagging, insight extraction, idea generation |
| Validation | `pydantic` — every LLM JSON response is schema-validated, with one automatic retry (validation error appended to the prompt) on failure |
| API | FastAPI, with interactive Swagger docs auto-generated at `/docs` |
| Frontend | React 18 + Vite, hand-rolled design system (no UI framework), mock-data fallback |

## Repo layout

```
main.py               one-shot manual ingestion run
tasks.py               Celery task version of ingestion (used by celery_app.py's schedule)
celery_app.py          Celery app + 30-minute beat schedule
sources.py             33 RSS sources across 13 domains
embed.py               sentence-transformers embedding helper
db.py                  Postgres connection, schema setup, article/insight/idea persistence, dedup
llm.py                 Gemini call wrapper: retry/backoff, quota-aware failure, temperature control
cluster.py             UMAP + HDBSCAN clustering, Gemini cluster tagging, CLI flags for iteration
schemas.py             pydantic models for LLM-output validation (Insight, Idea, IdeaList)
insights.py            insight extraction + idea generation per cluster, caching, Postgres persistence
prompts/               versioned prompt templates (insight_v1.txt, idea_v1.txt)
api.py                 FastAPI layer serving clusters/insights/ideas from Postgres
problem-radar-frontend/frontend/   React + Vite UI (see its own README for frontend-specific detail)
requirements.txt
dockercompose.yml      Postgres (pgvector) + Redis containers
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js (for the frontend)
- Docker Desktop
- A Gemini API key ([ai.google.dev](https://ai.google.dev))

### 1. Clone and install
```bash
git clone https://github.com/arushi-sharma-git/problem-radar.git
cd problem-radar
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Environment variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```

### 3. Start Postgres + Redis

If these containers don't already exist:
```bash
docker compose -f dockercompose.yml up -d
```
If you already created them individually (e.g. via `docker run`), just make sure they're running:
```bash
docker ps
```

### 4. Run the pipeline

**Ingest articles** (scrapes, embeds, dedupes, stores):
```bash
python main.py
```
Or run it continuously every 30 minutes via Celery:
```bash
celery -A celery_app worker --beat --loglevel=info
```

**Cluster articles into themes:**
```bash
python cluster.py
```
Useful flags for iterating without spending API quota:
```bash
python cluster.py --skip-llm                            # cluster only, no LLM tagging
python cluster.py --skip-llm --print-cluster 3           # inspect what's in cluster 3
python cluster.py --n-neighbors 8 --min-cluster-size 5   # tune clustering granularity
```

**Extract insights + generate ideas** (persists to Postgres):
```bash
python insights.py
```

**Serve the API:**
```bash
uvicorn api:app --reload
```
Open `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

**Run the frontend:**
```bash
cd problem-radar-frontend/frontend
npm install
npm run dev
```
Open `http://localhost:5173`. It talks to the API at `http://127.0.0.1:8000` by default (see that folder's `.env.example`), and automatically falls back to bundled mock data if the API isn't running — so the UI is always demoable even without the backend up.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /clusters` | All clusters with domain, confidence, article count |
| `GET /clusters/{cluster_id}/insight` | The extracted insight for one cluster |
| `GET /clusters/{cluster_id}/ideas` | The generated project ideas for one cluster |
| `GET /ideas?difficulty=beginner&domain=health` | Browse/filter ideas across all clusters |

## Design decisions worth noting

- **Domain-agnostic by design.** The pipeline deliberately spans science, climate, health, urban planning, design, finance, and society, not just AI/tech — and the prompts explicitly instruct the LLM not to force an AI angle onto a problem unless the evidence actually supports it.
- **HDBSCAN over k-means.** Cluster count isn't known in advance, and cluster sizes/densities vary a lot across domains. HDBSCAN handles both naturally, including correctly flagging outlier articles as noise instead of forcing them into an ill-fitting cluster.
- **Confidence field, not forced answers.** The insight-extraction prompt explicitly allows the model to report low confidence rather than invent a problem when a cluster doesn't cleanly resolve to one theme — this shows up in practice, with mixed clusters correctly flagged as low-confidence instead of confidently wrong.
- **Caching + prompt versioning.** LLM outputs are cached by cluster ID + prompt version, so iterating on a prompt doesn't require re-spending API quota on unchanged clusters, and bumping a prompt version cleanly invalidates only what needs to be recomputed.
- **Free-tier resilience.** LLM calls distinguish transient errors (retry with backoff) from quota exhaustion (fail fast rather than waste remaining quota retrying something that won't succeed).
- **A UI that works even when the backend doesn't.** The frontend ships with mock data matching the API's exact response shape, so it's always demoable — a genuinely useful property for a portfolio project, not just a development convenience.

## Status

All stages implemented and verified end-to-end: ingestion → embedding/dedup → clustering → tagging → insight extraction → idea generation → API → frontend. Currently running against 132 articles across 11 clusters, with 12 articles correctly identified as not fitting any coherent theme.
