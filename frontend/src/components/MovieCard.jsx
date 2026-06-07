import { posterUrl } from '../api'

export function fmtRuntime(ms) {
  if (!ms) return null
  const min = Math.round(ms / 60000)
  const h = Math.floor(min / 60)
  const m = min % 60
  return h ? `${h}h ${m}m` : `${m}m`
}

export default function MovieCard({ movie, className = '', gem = false, onClick }) {
  const src = posterUrl(movie.thumb)
  const rating = movie.audience_rating ?? movie.critic_rating
  return (
    <div className={`card ${className}`} onClick={onClick}>
      {src ? (
        <img className="poster" src={src} alt={movie.title} loading="lazy" />
      ) : (
        <div className="poster placeholder">{movie.title}</div>
      )}
      <div className="card-body">
        <div className="card-title">{movie.title}</div>
        <div className="card-meta">
          {movie.year && <span>{movie.year}</span>}
          {fmtRuntime(movie.duration_ms) && <span>{fmtRuntime(movie.duration_ms)}</span>}
          {rating ? <span className="badge">★ {rating.toFixed(1)}</span> : null}
          {gem && <span className="badge gem">💎 gem</span>}
          {!gem && movie.view_count > 0 && <span>· seen</span>}
        </div>
      </div>
    </div>
  )
}
