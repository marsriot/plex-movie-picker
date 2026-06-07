import { useState } from 'react'
import { api } from '../api'
import MovieCard from './MovieCard'

const SUGGESTIONS = [
  'rainy Sunday, cozy but a little sad',
  'high-energy, turn-my-brain-off action',
  'something funny for a tired weeknight',
  'mind-bending sci-fi that makes me think',
  'date night, romantic but not cheesy',
  'under 100 minutes and genuinely scary',
]

export default function Mood() {
  const [mood, setMood] = useState('')
  const [movies, setMovies] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [asked, setAsked] = useState(false)

  const ask = (text) => {
    const q = (text ?? mood).trim()
    if (!q) return
    setMood(q)
    setLoading(true)
    setError(null)
    setAsked(true)
    api.mood({ mood: q, count: 5 })
      .then((d) => setMovies(d.movies))
      .catch((e) => { setError(e.message); setMovies([]) })
      .finally(() => setLoading(false))
  }

  return (
    <div>
      <p className="section-intro">
        Describe the vibe you're after in plain English — Claude reads your whole
        library and picks a few that fit, with a reason for each.
      </p>

      <div className="filters">
        <input
          placeholder="e.g. rainy Sunday, cozy but a little sad, under 2 hours"
          value={mood}
          onChange={(e) => setMood(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          style={{ flex: 1, minWidth: 280 }}
        />
        <button className="btn-accent" onClick={() => ask()} disabled={loading}>
          {loading ? 'Thinking…' : '🎭 Find me something'}
        </button>
      </div>

      {!asked && (
        <div className="mood-chips">
          {SUGGESTIONS.map((s) => (
            <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>
          ))}
        </div>
      )}

      {error && <div className="error">{error}</div>}
      {loading && <div className="center muted">Reading the room and scanning your shelves…</div>}

      {!loading && movies.length > 0 && (
        <div className="mood-results">
          {movies.map((m) => (
            <div key={m.rating_key} className="mood-row">
              <MovieCard movie={m} className="mood-card" />
              {m.reason && <p className="mood-reason">“{m.reason}”</p>}
            </div>
          ))}
        </div>
      )}
      {!loading && asked && !error && movies.length === 0 && (
        <div className="center muted">No picks came back — try rephrasing the mood.</div>
      )}
    </div>
  )
}
