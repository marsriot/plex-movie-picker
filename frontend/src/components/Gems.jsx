import { useEffect, useState } from 'react'
import { api } from '../api'
import MovieCard from './MovieCard'

export default function Gems() {
  const [movies, setMovies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.gems({ limit: 40 })
      .then((d) => setMovies(d.movies))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <p className="section-intro">
        Highly-rated movies you own but have <strong>never watched</strong>, that have
        been sitting in your library a while. The good stuff you forgot about.
      </p>
      {error && <div className="error">{error}</div>}
      {loading ? (
        <div className="center muted">Digging through the vault…</div>
      ) : movies.length === 0 ? (
        <div className="center muted">No hidden gems found — sync your library first, or you’ve watched everything good!</div>
      ) : (
        <div className="grid">
          {movies.map((m) => <MovieCard key={m.rating_key} movie={m} gem />)}
        </div>
      )}
    </div>
  )
}
