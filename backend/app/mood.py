"""Mood-based movie picking via Claude.

We send Claude a compact catalog of the whole library (cached with prompt
caching so repeat queries are cheap) plus the user's plain-English mood, and ask
it to return a few picks with a one-line reason each. Claude returns rating_keys;
we map those back to full movie rows so the UI gets posters and metadata.
"""
import json
from typing import Any

from anthropic import Anthropic

from .config import settings
from .db import get_conn, row_to_movie

MODEL = "claude-sonnet-4-6"  # great mood-matching at lower cost; use claude-opus-4-8 for max quality

SYSTEM_INTRO = (
    "You are a film concierge with deep knowledge of cinema. You help someone decide "
    "what to watch tonight from THEIR OWN movie library, listed below. Each line is:\n"
    "[rating_key] Title (year) | genres | rating | runtime_min | watched?\n\n"
    "Only ever recommend movies from this list, identified by their exact rating_key. "
    "Use your knowledge of each film's tone, themes, and pacing to match the user's mood — "
    "don't just match genre keywords. Respect any hard constraints the user gives "
    "(runtime, watched/unwatched, etc.). Prefer unwatched films when it's a toss-up. "
    "Give a short, specific reason for each pick that speaks to why it fits THIS mood.\n\n"
    "=== LIBRARY ===\n"
)

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "picks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rating_key": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["rating_key", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["picks"],
    "additionalProperties": False,
}


def _runtime_min(ms: int | None) -> str:
    return str(round(ms / 60000)) if ms else "?"


def build_catalog() -> str:
    """Deterministic, compact one-line-per-movie catalog (stable for caching)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT rating_key, title, year, genres, audience_rating, critic_rating, "
            "duration_ms, view_count FROM movies ORDER BY rating_key"
        ).fetchall()
    lines = []
    for r in rows:
        genres = ", ".join(json.loads(r["genres"])) if r["genres"] else "—"
        rating = r["audience_rating"] or r["critic_rating"]
        rating_s = f"{rating:.1f}" if rating else "—"
        watched = "seen" if (r["view_count"] or 0) > 0 else "unwatched"
        year = r["year"] or "—"
        lines.append(
            f"[{r['rating_key']}] {r['title']} ({year}) | {genres} | "
            f"{rating_s} | {_runtime_min(r['duration_ms'])}min | {watched}"
        )
    return "\n".join(lines)


def pick_by_mood(mood: str, count: int = 5) -> list[dict[str, Any]]:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in backend/.env")

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    catalog = build_catalog()

    user_prompt = (
        f"My mood / what I'm after tonight: {mood}\n\n"
        f"Pick {count} movies from my library that fit. Return rating_keys and reasons."
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=[
            {
                "type": "text",
                "text": SYSTEM_INTRO + catalog,
                # Cache the (large, stable) catalog so repeat mood queries are cheap.
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
        output_config={"format": {"type": "json_schema", "schema": RESULT_SCHEMA}},
    )

    text = "".join(b.text for b in message.content if b.type == "text")
    picks = json.loads(text).get("picks", [])

    # Map rating_keys back to full movie rows, preserving Claude's order + reason.
    reasons = {p["rating_key"]: p.get("reason", "") for p in picks}
    keys = list(reasons.keys())
    if not keys:
        return []
    placeholders = ",".join("?" for _ in keys)
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM movies WHERE rating_key IN ({placeholders})", keys
        ).fetchall()
    by_key = {r["rating_key"]: row_to_movie(r) for r in rows}

    results = []
    for k in keys:
        if k in by_key:
            movie = by_key[k]
            movie["reason"] = reasons[k]
            results.append(movie)
    return results
