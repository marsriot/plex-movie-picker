"""Read queries against the local movie cache: filtering, sorting, hidden gems."""
import time
from typing import Any

from .db import get_conn, row_to_movie

SORTS = {
    "title": "title COLLATE NOCASE ASC",
    "year_desc": "year DESC",
    "year_asc": "year ASC",
    "rating": "COALESCE(audience_rating, critic_rating, 0) DESC",
    "added": "added_at DESC",
    "runtime_asc": "duration_ms ASC",
    "runtime_desc": "duration_ms DESC",
}


def list_movies(
    *,
    search: str | None = None,
    genre: str | None = None,
    unwatched: bool = False,
    max_runtime_min: int | None = None,
    min_year: int | None = None,
    sort: str = "title",
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    where = []
    params: list[Any] = []

    if search:
        where.append("title LIKE ?")
        params.append(f"%{search}%")
    if genre:
        where.append("genres LIKE ?")
        params.append(f'%"{genre}"%')
    if unwatched:
        where.append("COALESCE(view_count, 0) = 0")
    if max_runtime_min:
        where.append("duration_ms <= ?")
        params.append(max_runtime_min * 60_000)
    if min_year:
        where.append("year >= ?")
        params.append(min_year)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    order_sql = SORTS.get(sort, SORTS["title"])

    with get_conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS n FROM movies {where_sql}", params
        ).fetchone()["n"]
        rows = conn.execute(
            f"SELECT * FROM movies {where_sql} ORDER BY {order_sql} LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()

    return {"total": total, "movies": [row_to_movie(r) for r in rows]}


def all_genres() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT genres FROM movies WHERE genres IS NOT NULL").fetchall()
    counts: dict[str, int] = {}
    import json
    for r in rows:
        for g in json.loads(r["genres"]):
            counts[g] = counts.get(g, 0) + 1
    return [g for g, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def hidden_gems(limit: int = 30) -> list[dict[str, Any]]:
    """High-rated movies you own but have never watched, that have been sitting
    in the library for a while. Score = rating, lightly boosted by age in library.
    """
    six_months_ago = int(time.time()) - 180 * 86400
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT *,
                   COALESCE(audience_rating, critic_rating, 0) AS score
            FROM movies
            WHERE COALESCE(view_count, 0) = 0
              AND COALESCE(audience_rating, critic_rating, 0) >= 7.5
              AND (added_at IS NULL OR added_at <= ?)
            ORDER BY score DESC, added_at ASC
            LIMIT ?
            """,
            (six_months_ago, limit),
        ).fetchall()
    return [row_to_movie(r) for r in rows]


def random_pick(
    *,
    unwatched: bool = False,
    max_runtime_min: int | None = None,
    genre: str | None = None,
) -> dict[str, Any] | None:
    where = []
    params: list[Any] = []
    if unwatched:
        where.append("COALESCE(view_count, 0) = 0")
    if max_runtime_min:
        where.append("duration_ms <= ?")
        params.append(max_runtime_min * 60_000)
    if genre:
        where.append("genres LIKE ?")
        params.append(f'%"{genre}"%')
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT * FROM movies {where_sql} ORDER BY RANDOM() LIMIT 1", params
        ).fetchone()
    return row_to_movie(row) if row else None


def bracket_candidates(count: int = 8, unwatched: bool = False) -> list[dict[str, Any]]:
    where_sql = "WHERE COALESCE(view_count, 0) = 0" if unwatched else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM movies {where_sql} ORDER BY RANDOM() LIMIT ?", (count,)
        ).fetchall()
    return [row_to_movie(r) for r in rows]
