"""Offline demo playlist — no Apple API calls."""

from __future__ import annotations

import json
from pathlib import Path

from apple_music.client import Playlist, Track

DEMO_PATH = Path(__file__).resolve().parents[1] / "sample_data" / "playlist_demo.json"


def load_demo_playlist() -> Playlist:
    raw = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
    tracks = [Track(**t) for t in raw["tracks"]]
    return Playlist(id=raw["id"], name=raw["name"], tracks=tracks)


def demo_playlist_choices() -> list[tuple[str, str]]:
    pl = load_demo_playlist()
    return [(f"{pl.name} (demo)", pl.id)]
