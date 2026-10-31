"""Detect duplicate tracks in a playlist."""

from __future__ import annotations

from collections import defaultdict

from apple_music.client import Playlist, Track


def track_key(t: Track) -> str:
    if t.isrc:
        return f"isrc:{t.isrc.strip().upper()}"
    return f"name:{(t.name or '').strip().lower()}|artist:{(t.artist or '').strip().lower()}"


# Back-compat for internal callers
_key = track_key


def find_duplicates(playlist: Playlist) -> list[dict]:
    groups: dict[str, list[tuple[int, Track]]] = defaultdict(list)
    for idx, track in enumerate(playlist.tracks, start=1):
        groups[_key(track)].append((idx, track))

    dups = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        sample = items[0][1]
        dups.append(
            {
                "key": key,
                "title": sample.name,
                "artist": sample.artist,
                "count": len(items),
                "positions": [i for i, _ in items],
            }
        )
    dups.sort(key=lambda d: (-d["count"], d["title"].lower()))
    return dups


def format_duplicate_report(playlist: Playlist, dups: list[dict]) -> str:
    lines = [
        f"playlist  {playlist.name}",
        f"faixas    {len(playlist.tracks)}",
        f"duplicatas {len(dups)} grupo(s)",
        "─" * 44,
    ]
    if not dups:
        lines.append("ok · nenhuma música duplicada")
        return "\n".join(lines)
    for d in dups:
        pos = ", ".join(str(p) for p in d["positions"])
        lines.append(f"×{d['count']}  {d['title']} — {d['artist']}")
        lines.append(f"     posições: {pos}")
    return "\n".join(lines)
