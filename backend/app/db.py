"""SQLite cache of the Plex movie library.

We sync the library into this local DB so the app stays fast and works even when
Plex is slow or briefly unreachable.
"""
import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS movies (
    rating_key      TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    year            INTEGER,
    summary         TEXT,
    tagline         TEXT,
    duration_ms     INTEGER,
    genres          TEXT,   -- JSON array
    directors       TEXT,   -- JSON array
    actors          TEXT,   -- JSON array
    studio          TEXT,
    content_rating  TEXT,
    audience_rating REAL,   -- e.g. Rotten Tomatoes / IMDb-ish 0-10
    critic_rating   REAL,
    user_rating     REAL,   -- your own star rating (0-10)
    view_count      INTEGER DEFAULT 0,
    last_viewed_at  INTEGER, -- unix seconds
    added_at        INTEGER, -- unix seconds
    thumb           TEXT,
    art             TEXT
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def set_meta(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def get_meta(key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


def upsert_movies(movies: list[dict[str, Any]]) -> None:
    cols = [
        "rating_key", "title", "year", "summary", "tagline", "duration_ms",
        "genres", "directors", "actors", "studio", "content_rating",
        "audience_rating", "critic_rating", "user_rating", "view_count",
        "last_viewed_at", "added_at", "thumb", "art",
    ]
    placeholders = ", ".join("?" for _ in cols)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "rating_key")
    sql = (
        f"INSERT INTO movies ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(rating_key) DO UPDATE SET {updates}"
    )
    rows = []
    for m in movies:
        rows.append(tuple(
            json.dumps(m[c]) if c in ("genres", "directors", "actors") else m.get(c)
            for c in cols
        ))
    with get_conn() as conn:
        conn.executemany(sql, rows)


def replace_all_movies(movies: list[dict[str, Any]]) -> None:
    """Full refresh: clear and reinsert so deletions in Plex are reflected."""
    with get_conn() as conn:
        conn.execute("DELETE FROM movies")
    upsert_movies(movies)


def row_to_movie(row: sqlite3.Row) -> dict[str, Any]:
    m = dict(row)
    for field in ("genres", "directors", "actors"):
        m[field] = json.loads(m[field]) if m.get(field) else []
    return m
