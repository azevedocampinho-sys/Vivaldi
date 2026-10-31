"""Four Seasons studio façade — wired to Apple Music session + Ollama."""

from __future__ import annotations

import uuid
from typing import Any

from apple_music.client import Playlist
from four_seasons import composer, humming, instruments as inst_cat, notation, references
from four_seasons.session import Layer, Project, SEASONS

_PROJECT = Project()


def get_project() -> Project:
    return _PROJECT


def reset_project() -> Project:
    global _PROJECT
    _PROJECT = Project()
    return _PROJECT


def season_label(season_id: str) -> str:
    for sid, name, phase in SEASONS:
        if sid == season_id:
            return f"{name} · {phase}"
    return season_id


def set_season(season_id: str) -> str:
    _PROJECT.season = season_id
    _PROJECT.touch()
    return season_label(season_id)


def sync_apple_references(playlist: Playlist | None) -> str:
    data = references.analyze_playlist(playlist)
    _PROJECT.reference_summary = data["summary"]
    _PROJECT.reference_tracks = data.get("tracks") or []
    _PROJECT.touch()
    return data["summary"]


def update_preproduction(
    title: str,
    concept: str,
    mood: str,
    key: str,
    mode: str,
    tempo: float,
    playlist: Playlist | None,
) -> str:
    _PROJECT.title = (title or _PROJECT.title).strip() or "Sem título"
    _PROJECT.concept = (concept or "").strip()
    _PROJECT.mood = (mood or "").strip()
    _PROJECT.key = (key or "C").strip() or "C"
    _PROJECT.mode = (mode or "maior").strip() or "maior"
    _PROJECT.tempo_bpm = int(tempo or 100)
    sync_apple_references(playlist)
    _PROJECT.season = "spring"
    _PROJECT.touch()
    return (
        f"Primavera salva · {_PROJECT.title}\n"
        f"{_PROJECT.key} {_PROJECT.mode} · {_PROJECT.tempo_bpm} BPM\n"
        f"{_PROJECT.reference_summary}"
    )


def run_spring(model: str, playlist: Playlist | None) -> str:
    sync_apple_references(playlist)
    _PROJECT.season = "spring"
    return composer.spring_brief(_PROJECT, model)


def add_instrument(instrument_id: str) -> tuple[str, str]:
    meta = inst_cat.BY_ID.get(instrument_id)
    if not meta:
        return f"instrumento desconhecido: {instrument_id}", _PROJECT.layers_blob()
    if any(layer.instrument_id == instrument_id for layer in _PROJECT.layers):
        return f"já existe: {meta.name}", _PROJECT.layers_blob()
    _PROJECT.layers.append(
        Layer(
            id=f"L{uuid.uuid4().hex[:6]}",
            instrument_id=meta.id,
            instrument_name=meta.name,
        )
    )
    _PROJECT.touch()
    return f"+ {meta.name}", _PROJECT.layers_blob()


def remove_instrument(instrument_id: str) -> tuple[str, str]:
    before = len(_PROJECT.layers)
    _PROJECT.layers = [layer for layer in _PROJECT.layers if layer.instrument_id != instrument_id]
    removed = before - len(_PROJECT.layers)
    _PROJECT.touch()
    if removed:
        return f"removido {inst_cat.label(instrument_id)}", _PROJECT.layers_blob()
    return "instrumento não estava na rack", _PROJECT.layers_blob()


def ingest_humming(path: str | None) -> str:
    note = humming.analyze_humming(path)
    _PROJECT.humming_path = path
    _PROJECT.humming_notes = note
    _PROJECT.touch()
    return note


def run_summer(model: str, playlist: Playlist | None) -> tuple[str, str]:
    sync_apple_references(playlist)
    # Prefer richer prompt block in reference_summary area for composer
    data = references.analyze_playlist(playlist)
    if data.get("ok"):
        _PROJECT.reference_summary = data["prompt_block"]
    _PROJECT.season = "summer"
    text, _ = composer.summer_produce(_PROJECT, model)
    return text, _PROJECT.layers_blob()


def run_autumn_chat(
    message: str,
    history: list,
    model: str,
    playlist: Playlist | None,
) -> tuple[list[dict[str, str]], list[tuple[str, str]], str]:
    sync_apple_references(playlist)
    data = references.analyze_playlist(playlist)
    if data.get("ok"):
        _PROJECT.reference_summary = data["prompt_block"]
    _PROJECT.season = "autumn"
    pairs: list[tuple[str, str]] = []
    if history:
        if isinstance(history[0], dict):
            user_buf = None
            for item in history:
                if item.get("role") == "user":
                    user_buf = item.get("content", "")
                elif item.get("role") == "assistant" and user_buf is not None:
                    pairs.append((user_buf, item.get("content", "")))
                    user_buf = None
        else:
            pairs = [(a, b) for a, b in history]
    answer, pairs, _ = composer.autumn_chat(_PROJECT, message, pairs, model)
    messages = []
    for q, a in pairs:
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a})
    return messages, pairs, _PROJECT.layers_blob()


def run_winter(model: str, playlist: Playlist | None) -> tuple[str, str, str]:
    sync_apple_references(playlist)
    _PROJECT.season = "winter"
    mix = composer.winter_finish(_PROJECT, model)
    scores, paths = notation.export_scores(_PROJECT)
    saved = _PROJECT.save()
    status = (
        f"Projeto salvo: {saved}\n"
        f"Scores: {paths[0].parent if paths else '—'}\n"
        f"{len(_PROJECT.layers)} instrumento(s)"
    )
    return mix, scores, status


def layers_view() -> str:
    return _PROJECT.layers_blob()


def project_status() -> str:
    return (
        f"{_PROJECT.title} · {season_label(_PROJECT.season)}\n"
        f"{_PROJECT.key} {_PROJECT.mode} · {_PROJECT.tempo_bpm} BPM · "
        f"{len(_PROJECT.layers)} camada(s)\n"
        f"{_PROJECT.reference_summary.splitlines()[0] if _PROJECT.reference_summary else 'sem refs Apple Music'}"
    )
