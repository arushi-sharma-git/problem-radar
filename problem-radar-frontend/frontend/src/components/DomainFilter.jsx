export default function DomainFilter({ domains, total, active, onSelect }) {
  return (
    <div className="category-filter">
      <span className="category-filter-label">Filter by domain</span>
      <div className="category-chip-row">
        <button
          className={`category-chip ${active === 'All' ? 'active' : ''}`}
          onClick={() => onSelect('All')}
        >
          All
          <span className="category-chip-count">{total}</span>
        </button>
        {domains.map((d) => (
          <button
            key={d.name}
            className={`category-chip ${active === d.name ? 'active' : ''}`}
            onClick={() => onSelect(d.name)}
          >
            {d.name}
            <span className="category-chip-count">{d.count}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
