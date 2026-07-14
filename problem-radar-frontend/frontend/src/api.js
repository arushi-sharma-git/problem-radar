import { MOCK_CLUSTERS, MOCK_INSIGHTS, MOCK_IDEAS } from './mockData'

// Matches api.py: uvicorn runs on 127.0.0.1:8000 by default, CORS is wide
// open (allow_origins=["*"]), so the frontend can call it directly with no
// dev-server proxy needed.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

async function safeFetch(path) {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) {
    // api.py's exception handler always returns {"detail": "..."} on errors
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      /* body wasn't JSON, fall back to statusText */
    }
    throw new Error(detail)
  }
  return res.json()
}

// GET /clusters -> ClusterSummary[]
export async function fetchClusters() {
  if (USE_MOCKS) return simulateLatency(MOCK_CLUSTERS)
  try {
    return await safeFetch('/clusters')
  } catch (err) {
    console.warn('[api] falling back to mock clusters:', err.message)
    return simulateLatency(MOCK_CLUSTERS)
  }
}

// GET /clusters/{id}/insight -> InsightOut
export async function fetchClusterInsight(clusterId) {
  if (USE_MOCKS) return simulateLatency(MOCK_INSIGHTS[clusterId] ?? null)
  try {
    return await safeFetch(`/clusters/${clusterId}/insight`)
  } catch (err) {
    console.warn('[api] falling back to mock insight:', err.message)
    return simulateLatency(MOCK_INSIGHTS[clusterId] ?? null)
  }
}

// GET /clusters/{id}/ideas -> IdeaOut[]
export async function fetchClusterIdeas(clusterId) {
  if (USE_MOCKS) return simulateLatency(MOCK_IDEAS[clusterId] ?? [])
  try {
    return await safeFetch(`/clusters/${clusterId}/ideas`)
  } catch (err) {
    console.warn('[api] falling back to mock ideas:', err.message)
    return simulateLatency(MOCK_IDEAS[clusterId] ?? [])
  }
}

// GET /ideas?difficulty=&domain= -> IdeaOut[]
// Not used by the main cluster-by-cluster view, but exposed for a future
// "browse all ideas" screen since the backend already supports it.
export async function fetchAllIdeas({ difficulty, domain } = {}) {
  const params = new URLSearchParams()
  if (difficulty) params.set('difficulty', difficulty)
  if (domain) params.set('domain', domain)
  const qs = params.toString() ? `?${params.toString()}` : ''

  if (USE_MOCKS) {
    let all = Object.values(MOCK_IDEAS).flat()
    if (difficulty) all = all.filter((i) => i.difficulty === difficulty)
    return simulateLatency(all)
  }
  try {
    return await safeFetch(`/ideas${qs}`)
  } catch (err) {
    console.warn('[api] falling back to mock ideas list:', err.message)
    let all = Object.values(MOCK_IDEAS).flat()
    if (difficulty) all = all.filter((i) => i.difficulty === difficulty)
    return simulateLatency(all)
  }
}

function simulateLatency(data, ms = 300) {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms))
}
