import { useEffect, useState } from 'react'
import { api } from '../api'
import MovieCard from './MovieCard'

export default function Browse() {
  const [genres, setGenres] = useState([])
  const [filters, setFilters] = useState({
    search: '', genre: '', unwatched: false, max_runtime_min: '', sort: 'title',
  })
  const [data, setData] = useState({ movies: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => { api.genres().then((d) => setGenres(d.genres)).catch(() => {}) }, [])

  useEffect(() => {
    setLoading(true)
    const t = setTimeout(() => {
      api.movies(filters)
        .then((d) => { setData(d); setError(null) })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false))
    }, 250) // debounce typing
    return () => clearTimeout(t)
  }, [filters])

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setFilters((f) => ({ ...f, [k]: v }))
  }

  return (
    <div>
      <div className="filters">
        <input placeholder="Search titles…" value={filters.search} onChange={set('search')} style={{ minWidth: 200 }} />
        <select value={filters.genre} onChange={set('genre')}>
          <option value="">All genres</option>
          {genres.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
        <select value={filters.max_runtime_min} onChange={set('max_runtime_min')}>
          <option value="">Any length</option>
          <option value="90">≤ 90 min</option>
          <option value="120">≤ 2 hours</option>
          <option value="150">≤ 2.5 hours</option>
        </select>
        <select value={filters.sort} onChange={set('sort')}>
          <option value="title">Title A–Z</option>
          <option value="rating">Top rated</option>
          <option value="year_desc">Newest</option>
          <option value="year_asc">Oldest</option>
          <option value="added">Recently added</option>
          <option value="runtime_asc">Shortest</option>
        </select>
        <label className="checkbox">
          <input type="checkbox" checked={filters.unwatched} onChange={set('unwatched')} />
          Unwatched only
        </label>
        <span className="spacer" />
        <span className="muted" style={{ fontSize: '0.85rem' }}>{data.total} movies</span>
      </div>

      {error && <div className="error">{error}</div>}
      {loading ? (
        <div className="center muted">Loading…</div>
      ) : data.movies.length === 0 ? (
        <div className="center muted">No movies match those filters.</div>
      ) : (
        <div className="grid">
          {data.movies.map((m) => <MovieCard key={m.rating_key} movie={m} />)}
        </div>
      )}
    </div>
  )
}
