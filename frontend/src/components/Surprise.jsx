import { useState } from 'react'
import { api } from '../api'
import MovieCard from './MovieCard'

export default function Surprise() {
  const [opts, setOpts] = useState({ unwatched: true, max_runtime_min: '' })
  const [movie, setMovie] = useState(null)
  const [error, setError] = useState(null)
  const [spinning, setSpinning] = useState(false)

  const roll = () => {
    setSpinning(true)
    setError(null)
    api.random(opts)
      .then(setMovie)
      .catch((e) => { setError(e.message); setMovie(null) })
      .finally(() => setSpinning(false))
  }

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setOpts((o) => ({ ...o, [k]: v }))
  }

  return (
    <div className="surprise-stage">
      <p className="section-intro" style={{ textAlign: 'center' }}>
        Can’t decide? Let the projector pick. One movie, no scrolling.
      </p>
      <div className="filters" style={{ justifyContent: 'center' }}>
        <label className="checkbox">
          <input type="checkbox" checked={opts.unwatched} onChange={set('unwatched')} />
          Unwatched only
        </label>
        <select value={opts.max_runtime_min} onChange={set('max_runtime_min')}>
          <option value="">Any length</option>
          <option value="90">≤ 90 min</option>
          <option value="120">≤ 2 hours</option>
          <option value="150">≤ 2.5 hours</option>
        </select>
      </div>

      <button className="btn-accent" onClick={roll} disabled={spinning} style={{ fontSize: '1.05rem', padding: '12px 28px' }}>
        {spinning ? 'Rolling…' : movie ? '🎲 Roll again' : '🎲 Surprise me'}
      </button>

      {error && <div className="error">{error}</div>}
      {movie && (
        <>
          <MovieCard movie={movie} className="surprise-card" />
          {movie.summary && <p className="surprise-summary">{movie.summary}</p>}
        </>
      )}
    </div>
  )
}
