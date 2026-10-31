"""Filter playlist tracks by year / genre."""

from __future__ import annotations

from apple_music.client import Playlist, Track


def available_genres(playlist: Playlist) -> list[str]:
    genres = sorted({(t.genre or "—") for t in playlist.tracks})
    return genres


def available_years(playlist: Playlist) -> list[str]:
    years = sorted({str(t.year) for t in playlist.tracks if t.year}, reverse=True)
    return years


def apply_filters(
    playlist: Playlist,
    *,
    year: str | None = None,
    genre: str | None = None,
) -> list[Track]:
    tracks = list(playlist.tracks)
    if year and year not in ("", "todos", "Todos"):
        tracks = [t for t in tracks if t.year is not None and str(t.year) == str(year)]
    if genre and genre not in ("", "todos", "Todos", "—"):
        tracks = [t for t in tracks if (t.genre or "").lower() == genre.lower()]
    return tracks


def format_track_table(tracks: list[Track], limit: int = 80) -> str:
    if not tracks:
        return "(nenhuma faixa com esses filtros)"
    lines = [f"#  título — artista  ·  ano  ·  gênero", "─" * 44]
    for i, t in enumerate(tracks[:limit], start=1):
        y = t.year or "?"
        lines.append(f"{i:>2}  {t.name} — {t.artist}  ·  {y}  ·  {t.genre}")
    if len(tracks) > limit:
        lines.append(f"… +{len(tracks) - limit} faixas")
    return "\n".join(lines)
