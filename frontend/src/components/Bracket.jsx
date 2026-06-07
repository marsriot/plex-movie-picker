import { useState } from 'react'
import { api } from '../api'
import MovieCard from './MovieCard'

export default function Bracket() {
  const [size, setSize] = useState(8)
  const [unwatched, setUnwatched] = useState(true)
  const [round, setRound] = useState([])     // contestants in current round
  const [next, setNext] = useState([])       // winners advancing
  const [pair, setPair] = useState(0)        // index of current matchup
  const [winner, setWinner] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const start = () => {
    setLoading(true)
    setError(null)
    setWinner(null)
    api.bracket({ count: size, unwatched })
      .then((d) => {
        if (d.movies.length < 2) throw new Error('Not enough movies for a bracket.')
        setRound(d.movies)
        setNext([])
        setPair(0)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  const choose = (m) => {
    const advancing = [...next, m]
    const nextPair = pair + 2
    if (nextPair >= round.length) {
      // round finished
      if (advancing.length === 1) {
        setWinner(advancing[0])
        setRound([])
        return
      }
      setRound(advancing)
      setNext([])
      setPair(0)
    } else {
      setNext(advancing)
      setPair(nextPair)
    }
  }

  const active = round.length > 0
  const a = round[pair]
  const b = round[pair + 1]
  const remaining = round.length + next.length

  return (
    <div className="bracket-stage">
      <p className="section-intro" style={{ textAlign: 'center' }}>
        Head-to-head. Pick the one you’d rather watch; the winner advances until one
        movie is left standing.
      </p>

      {!active && !winner && (
        <>
          <div className="filters" style={{ justifyContent: 'center' }}>
            <select value={size} onChange={(e) => setSize(Number(e.target.value))}>
              <option value={4}>4 movies</option>
              <option value={8}>8 movies</option>
              <option value={16}>16 movies</option>
            </select>
            <label className="checkbox">
              <input type="checkbox" checked={unwatched} onChange={(e) => setUnwatched(e.target.checked)} />
              Unwatched only
            </label>
          </div>
          <button className="btn-accent" onClick={start} disabled={loading} style={{ fontSize: '1.05rem', padding: '12px 28px' }}>
            {loading ? 'Loading…' : '⚔️ Start bracket'}
          </button>
        </>
      )}

      {error && <div className="error">{error}</div>}

      {active && a && b && (
        <>
          <div className="bracket-progress">{remaining} left · this or that?</div>
          <div className="versus">
            <MovieCard movie={a} className="vs-pick" onClick={() => choose(a)} />
            <span className="vs-label">VS</span>
            <MovieCard movie={b} className="vs-pick" onClick={() => choose(b)} />
          </div>
        </>
      )}

      {winner && (
        <>
          <div className="winner-banner">🏆 Tonight’s winner</div>
          <MovieCard movie={winner} className="surprise-card" />
          {winner.summary && <p className="surprise-summary">{winner.summary}</p>}
          <button onClick={start} className="btn-accent">Run it again</button>
        </>
      )}
    </div>
  )
}
