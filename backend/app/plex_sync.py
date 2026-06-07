"""Pull the movie library from Plex into the local SQLite cache."""
import time
from typing import Any

from plexapi.server import PlexServer

from .config import settings
from .db import get_meta, replace_all_movies, set_meta


def _to_unix(dt: Any) -> int | None:
    if not dt:
        return None
    try:
        return int(dt.timestamp())
    except (AttributeError, OSError, ValueError):
        return None


def _movie_to_dict(movie: Any) -> dict[str, Any]:
    return {
        "rating_key": str(movie.ratingKey),
        "title": movie.title,
        "year": getattr(movie, "year", None),
        "summary": getattr(movie, "summary", None),
        "tagline": getattr(movie, "tagline", None),
        "duration_ms": getattr(movie, "duration", None),
        "genres": [g.tag for g in getattr(movie, "genres", [])],
        "directors": [d.tag for d in getattr(movie, "directors", [])],
        "actors": [r.tag for r in getattr(movie, "roles", [])][:10],
        "studio": getattr(movie, "studio", None),
        "content_rating": getattr(movie, "contentRating", None),
        "audience_rating": getattr(movie, "audienceRating", None),
        "critic_rating": getattr(movie, "rating", None),
        "user_rating": getattr(movie, "userRating", None),
        "view_count": getattr(movie, "viewCount", 0) or 0,
        "last_viewed_at": _to_unix(getattr(movie, "lastViewedAt", None)),
        "added_at": _to_unix(getattr(movie, "addedAt", None)),
        "thumb": getattr(movie, "thumb", None),
        "art": getattr(movie, "art", None),
    }


def connect() -> PlexServer:
    if not settings.plex_configured:
        raise RuntimeError("Plex is not configured. Set PLEX_URL and PLEX_TOKEN in backend/.env")
    return PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)


def sync_library() -> dict[str, Any]:
    """Full refresh of the movie cache from Plex. Returns a summary."""
    plex = connect()
    section = plex.library.section(settings.PLEX_MOVIE_LIBRARY)
    movies = [_movie_to_dict(m) for m in section.all()]
    replace_all_movies(movies)
    set_meta("last_sync", str(int(time.time())))
    set_meta("movie_count", str(len(movies)))
    return {"count": len(movies), "last_sync": int(time.time())}


def last_sync_info() -> dict[str, Any]:
    ls = get_meta("last_sync")
    return {
        "last_sync": int(ls) if ls else None,
        "movie_count": int(get_meta("movie_count") or 0),
    }
