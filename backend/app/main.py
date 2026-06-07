"""FastAPI app: serves the movie-picker API (and the built frontend, if present)."""
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import queries
from .config import settings
from .db import init_db
from .mood import pick_by_mood
from .plex_sync import last_sync_info, sync_library

app = FastAPI(title="Movie Picker")

# Allow the Vite dev server to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/status")
def status() -> dict:
    return {
        "plex_configured": settings.plex_configured,
        "llm_configured": bool(settings.ANTHROPIC_API_KEY),
        **last_sync_info(),
    }


@app.post("/api/sync")
def sync() -> dict:
    if not settings.plex_configured:
        raise HTTPException(400, "Plex is not configured. Set PLEX_URL and PLEX_TOKEN in backend/.env")
    try:
        return sync_library()
    except Exception as e:  # noqa: BLE001 - surface the real reason to the UI
        raise HTTPException(502, f"Sync failed: {e}")


@app.get("/api/movies")
def movies(
    search: str | None = None,
    genre: str | None = None,
    unwatched: bool = False,
    max_runtime_min: int | None = None,
    min_year: int | None = None,
    sort: str = "title",
    limit: int = Query(200, le=500),
    offset: int = 0,
) -> dict:
    return queries.list_movies(
        search=search, genre=genre, unwatched=unwatched,
        max_runtime_min=max_runtime_min, min_year=min_year,
        sort=sort, limit=limit, offset=offset,
    )


@app.get("/api/genres")
def genres() -> dict:
    return {"genres": queries.all_genres()}


@app.get("/api/gems")
def gems(limit: int = Query(30, le=100)) -> dict:
    return {"movies": queries.hidden_gems(limit=limit)}


@app.get("/api/random")
def random(
    unwatched: bool = False,
    max_runtime_min: int | None = None,
    genre: str | None = None,
) -> dict:
    movie = queries.random_pick(
        unwatched=unwatched, max_runtime_min=max_runtime_min, genre=genre
    )
    if not movie:
        raise HTTPException(404, "No movies match those filters.")
    return movie


@app.get("/api/bracket")
def bracket(count: int = Query(8, ge=2, le=32), unwatched: bool = False) -> dict:
    return {"movies": queries.bracket_candidates(count=count, unwatched=unwatched)}


class MoodRequest(BaseModel):
    mood: str
    count: int = 5


@app.post("/api/mood")
def mood(req: MoodRequest) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(400, "ANTHROPIC_API_KEY is not set in backend/.env")
    if not req.mood.strip():
        raise HTTPException(400, "Tell me a mood first.")
    try:
        picks = pick_by_mood(req.mood.strip(), count=max(1, min(req.count, 8)))
    except Exception as e:  # noqa: BLE001 - surface the real reason to the UI
        raise HTTPException(502, f"Mood pick failed: {e}")
    return {"movies": picks}


@app.get("/api/poster")
def poster(path: str) -> Response:
    """Proxy a Plex image so the auth token stays server-side."""
    if not settings.plex_configured:
        raise HTTPException(400, "Plex not configured")
    if not path.startswith("/"):
        raise HTTPException(400, "Invalid path")
    url = f"{settings.PLEX_URL.rstrip('/')}{path}"
    try:
        r = httpx.get(url, params={"X-Plex-Token": settings.PLEX_TOKEN}, timeout=15)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Could not fetch image: {e}")
    return Response(
        content=r.content,
        media_type=r.headers.get("content-type", "image/jpeg"),
        headers={"Cache-Control": "public, max-age=86400"},
    )


# Serve the built frontend if it exists (production / single-process mode).
_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
