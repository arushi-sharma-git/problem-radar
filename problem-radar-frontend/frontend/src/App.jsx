import { useEffect, useMemo, useState } from 'react'
import { fetchClusters, fetchClusterInsight, fetchClusterIdeas } from './api'
import ClusterCard from './components/ClusterCard'
import ClusterDetailPanel from './components/ClusterDetailPanel'
import DomainFilter from './components/DomainFilter'

export default function App() {
  const [clusters, setClusters] = useState([])
  const [loadingClusters, setLoadingClusters] = useState(true)
  const [apiError, setApiError] = useState(null)

  const [selectedClusterId, setSelectedClusterId] = useState(null)
  const [insight, setInsight] = useState(null)
  const [ideas, setIdeas] = useState([])
  const [loadingDetail, setLoadingDetail] = useState(false)

  const [query, setQuery] = useState('')
  const [activeDomain, setActiveDomain] = useState('All')

  // Load the cluster list once on mount — mirrors loadClusters() in frontend.html
  useEffect(() => {
    let cancelled = false
    setLoadingClusters(true)
    fetchClusters()
      .then((data) => {
        if (cancelled) return
        setClusters(data)
        setApiError(null)
        if (data.length > 0) setSelectedClusterId(data[0].cluster_id)
      })
      .catch((err) => setApiError(err.message))
      .finally(() => !cancelled && setLoadingClusters(false))
    return () => {
      cancelled = true
    }
  }, [])

  // Load insight + ideas together whenever the selected cluster changes —
  // mirrors selectCluster()'s Promise.all([insight, ideas]) in frontend.html
  useEffect(() => {
    if (selectedClusterId == null) return
    let cancelled = false
    setLoadingDetail(true)
    Promise.all([
      fetchClusterInsight(selectedClusterId),
      fetchClusterIdeas(selectedClusterId),
    ])
      .then(([insightData, ideasData]) => {
        if (cancelled) return
        setInsight(insightData)
        setIdeas(ideasData)
      })
      .finally(() => !cancelled && setLoadingDetail(false))
    return () => {
      cancelled = true
    }
  }, [selectedClusterId])

  const domains = useMemo(() => {
    const counts = {}
    clusters.forEach((c) => {
      counts[c.domain] = (counts[c.domain] ?? 0) + 1
    })
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
  }, [clusters])

  const filteredClusters = useMemo(() => {
    let list = [...clusters]
    if (activeDomain !== 'All') {
      list = list.filter((c) => c.domain === activeDomain)
    }
    if (query.trim()) {
      const q = query.toLowerCase()
      list = list.filter((c) => c.domain.toLowerCase().includes(q))
    }
    return list
  }, [clusters, query, activeDomain])

  const selectedCluster = clusters.find((c) => c.cluster_id === selectedClusterId) ?? null

  return (
    <div className="app">
      <header className="topbar">
        <div className="wordmark">
          PROBLEM<span className="dot">·</span>RADAR
        </div>
        <div className={`status-pill ${apiError ? 'error' : ''}`}>
          <span className="pulse-dot" />
          {apiError ? 'API unreachable — showing mock data' : 'connected'}
        </div>
        <div className="searchbar">
          <span aria-hidden="true">⌕</span>
          <input
            type="text"
            placeholder="Filter clusters by domain…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Filter clusters"
          />
        </div>
      </header>

      <DomainFilter
        domains={domains}
        total={clusters.length}
        active={activeDomain}
        onSelect={setActiveDomain}
      />

      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar-heading">
            <span>Clusters</span>
            <span>{filteredClusters.length}</span>
          </div>
          {loadingClusters && (
            <div className="loading-state" style={{ padding: '40px 10px' }}>
              <div className="scan-line" />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                Loading clusters…
              </span>
            </div>
          )}
          {!loadingClusters && filteredClusters.length === 0 && (
            <div className="empty-state" style={{ padding: '40px 10px' }}>
              <div className="empty-state-title">No matches</div>
              <p style={{ fontSize: 13, maxWidth: 260 }}>
                Nothing matches "{query}". Try a different term or domain.
              </p>
            </div>
          )}
          {!loadingClusters &&
            filteredClusters.map((cluster) => (
              <ClusterCard
                key={cluster.cluster_id}
                cluster={cluster}
                active={cluster.cluster_id === selectedClusterId}
                onSelect={setSelectedClusterId}
              />
            ))}
        </aside>

        <main className="main">
          <ClusterDetailPanel
            cluster={selectedCluster}
            insight={insight}
            ideas={ideas}
            loading={loadingDetail}
          />
        </main>
      </div>
    </div>
  )
}
