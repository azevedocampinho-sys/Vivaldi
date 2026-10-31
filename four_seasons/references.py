"""Extract musical DNA from Apple Music playlists for Four Seasons."""

from __future__ import annotations

from collections import Counter
from typing import Any

from apple_music.client import Playlist


def analyze_playlist(playlist: Playlist | None) -> dict[str, Any]:
    if not playlist or not playlist.tracks:
        return {
            "ok": False,
            "summary": "Nenhuma playlist Apple Music carregada. Abra uma no estúdio Apple Music e volte.",
            "tracks": [],
            "artists": [],
            "genres": [],
            "years": [],
            "prompt_block": "Sem referências de playlist.",
        }

    artists = Counter((t.artist or "?").strip() for t in playlist.tracks)
    genres = Counter((t.genre or "—").strip() for t in playlist.tracks)
    years = [t.year for t in playlist.tracks if t.year]
    top_artists = [a for a, _ in artists.most_common(8)]
    top_genres = [g for g, _ in genres.most_common(6)]
    year_span = f"{min(years)}–{max(years)}" if years else "—"
    sample = [
        {
            "title": t.name,
            "artist": t.artist,
            "album": t.album,
            "year": t.year,
            "genre": t.genre,
        }
        for t in playlist.tracks[:24]
    ]
    summary = (
        f"Playlist “{playlist.name}” · {len(playlist.tracks)} faixas · anos {year_span}\n"
        f"Artistas-chave: {', '.join(top_artists[:5]) or '—'}\n"
        f"Gêneros: {', '.join(top_genres) or '—'}"
    )
    prompt_block = (
        f"REFERÊNCIAS APPLE MUSIC (playlist do usuário):\n"
        f"Nome: {playlist.name}\n"
        f"Artistas dominantes: {', '.join(top_artists)}\n"
        f"Gêneros: {', '.join(top_genres)}\n"
        f"Janela temporal: {year_span}\n"
        f"Amostra de faixas:\n"
        + "\n".join(
            f"- {t['title']} — {t['artist']}"
            + (f" ({t['year']})" if t.get("year") else "")
            for t in sample[:16]
        )
        + "\nUse estas referências como DNA estético (harmonia, energia, timbre). "
        "Não copie melodias protegidas; inspire-se no clima e na linguagem."
    )
    return {
        "ok": True,
        "summary": summary,
        "tracks": sample,
        "artists": top_artists,
        "genres": top_genres,
        "years": years,
        "prompt_block": prompt_block,
        "playlist_name": playlist.name,
        "track_count": len(playlist.tracks),
    }
