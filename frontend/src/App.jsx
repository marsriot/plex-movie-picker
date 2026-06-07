import { useEffect, useState } from 'react'
import { api } from './api'
import Mood from './components/Mood'
import Browse from './components/Browse'
import Gems from './components/Gems'
import Surprise from './components/Surprise'
import Bracket from './components/Bracket'

const TABS = [
  { id: 'mood', label: '🎭 Mood', el: Mood },
  { id: 'surprise', label: '🎲 Surprise Me', el: Surprise },
  { id: 'bracket', label: '⚔️ Bracket', el: Bracket },
  { id: 'gems', label: '💎 Hidden Gems', el: Gems },
  { id: 'browse', label: '🎬 Browse', el: Browse },
]

function ReelIcon() {
  return (
    <svg className="reel-icon" viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="32" cy="32" r="21" fill="none" stroke="currentColor" strokeWidth="4" />
      <g fill="currentColor">
        <circle cx="32" cy="32" r="5.5" />
        <circle cx="44" cy="32" r="3.4" />
        <circle cx="38" cy="21.6" r="3.4" />
        <circle cx="26" cy="21.6" r="3.4" />
        <circle cx="20" cy="32" r="3.4" />
        <circle cx="26" cy="42.4" r="3.4" />
        <circle cx="38" cy="42.4" r="3.4" />
      </g>
    </svg>
  )
}

function timeAgo(unix) {
  if (!unix) return 'never'
  const s = Math.floor(Date.now() / 1000) - unix
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

export default function App() {
  const [tab, setTab] = useState('mood')
  const [status, setStatus] = useState(null)
  const [syncing, setSyncing] = useState(false)
  const [syncMsg, setSyncMsg] = useState(null)

  const refresh = () => api.status().then(setStatus).catch(() => setStatus({ plex_configured: false }))
  useEffect(() => { refresh() }, [])

  const sync = async () => {
    setSyncing(true)
    setSyncMsg(null)
    try {
      const r = await api.sync()
      setSyncMsg(`Synced ${r.count} movies`)
      await refresh()
    } catch (e) {
      setSyncMsg(e.message)
    } finally {
      setSyncing(false)
    }
  }

  const Active = TABS.find((t) => t.id === tab).el
  const empty = status && status.movie_count === 0

  return (
    <>
      <div className="filmstrip" />
      <div className="app">
      <div className="topbar">
        <div className="brand">
          <ReelIcon />
          <div className="brand-text">
            <span className="wordmark">REEL PICK</span>
            <span className="tagline">🍿 what should we watch tonight?</span>
          </div>
        </div>
        <span className="spacer" />
        {status && (
          <span className="status-pill">
            <span className={`dot ${status.plex_configured ? 'on' : 'off'}`} />
            {status.plex_configured
              ? <>{status.movie_count} movies · synced {timeAgo(status.last_sync)}</>
              : 'Plex not configured'}
          </span>
        )}
        <button onClick={sync} disabled={syncing || !status?.plex_configured}>
          {syncing ? 'Syncing…' : '↻ Sync'}
        </button>
      </div>
      {syncMsg && <div className="muted" style={{ fontSize: '0.82rem', textAlign: 'right' }}>{syncMsg}</div>}

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t.id} className={`tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {status && !status.plex_configured ? (
        <div className="center">
          <p className="muted">
            Plex isn’t connected yet. Add your <code>PLEX_URL</code> and <code>PLEX_TOKEN</code> to
            <code> backend/.env</code>, restart the backend, then hit Sync.
          </p>
        </div>
      ) : empty ? (
        <div className="center">
          <p className="muted">Your library cache is empty. Hit <strong>↻ Sync</strong> to pull your movies from Plex.</p>
          <button className="btn-accent" onClick={sync} disabled={syncing}>{syncing ? 'Syncing…' : 'Sync now'}</button>
        </div>
      ) : (
        <Active />
      )}
      </div>
    </>
  )
}
