"""Apply playlist hygiene to Apple Music via the official write API.

Apple's public MusicKit HTTP API allows creating playlists and adding tracks.
Removing/reordering tracks on an existing playlist is blocked (403/401) for
normal developer tokens — so the supported one-click path is: create a new
library playlist with the cleaned / reordered track list.
"""

from __future__ import annotations

from apple_music.client import AppleMusicClient, Playlist, Track
from apple_music import duplicates


def deduped_tracks(playlist: Playlist) -> tuple[list[Track], int]:
    """Keep first occurrence of each duplicate group. Returns (tracks, removed_count)."""
    seen: set[str] = set()
    kept: list[Track] = []
    removed = 0
    for track in playlist.tracks:
        key = duplicates._key(track)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        kept.append(track)
    return kept, removed


def duplicate_track_ids_to_drop(playlist: Playlist) -> list[str]:
    """Ids of later duplicates (positions after the first keep)."""
    seen: set[str] = set()
    drop: list[str] = []
    for track in playlist.tracks:
        key = duplicates._key(track)
        if key in seen:
            if track.id:
                drop.append(track.id)
            continue
        seen.add(key)
    return drop


def apply_remove_duplicates(
    client: AppleMusicClient,
    playlist: Playlist,
    *,
    new_name: str | None = None,
) -> str:
    kept, removed = deduped_tracks(playlist)
    if removed == 0:
        return f"ok · {playlist.name} já está sem duplicatas ({len(playlist.tracks)} faixas)"

    if not client.configured:
        return (
            f"demo · removeria {removed} duplicata(s), ficariam {len(kept)} faixas. "
            "Conecte tokens na área Conexão para gravar no Apple Music."
        )

    # 1) Try in-place delete (usually blocked by Apple)
    drop_ids = duplicate_track_ids_to_drop(playlist)
    ok, detail = client.try_remove_tracks(playlist.id, drop_ids)
    if ok:
        client.invalidate_playlist_cache(playlist.id)
        return (
            f"✓ Apple Music atualizado · {detail}\n"
            f"playlist original: {playlist.name}\n"
            f"antes {len(playlist.tracks)} → agora ~{len(kept)} faixas"
        )

    # 2) Official path: create cleaned playlist
    name = (new_name or f"{playlist.name} · limpa").strip()
    created = client.create_library_playlist(
        name,
        kept,
        description=f"Vivaldi · sem duplicatas (origem: {playlist.name})",
    )
    return (
        f"✓ Criada no Apple Music: “{created.name}”\n"
        f"id {created.id}\n"
        f"removidas {removed} duplicata(s) · {len(kept)} faixas\n"
        f"nota: {detail}\n"
        "A playlist original permanece intacta (limitação da API Apple). "
        "Use a nova playlist limpa no app Música."
    )


def apply_track_order(
    client: AppleMusicClient,
    playlist: Playlist,
    ordered: list[Track],
    *,
    new_name: str | None = None,
) -> str:
    if not ordered:
        return "nenhuma faixa na ordem sugerida"
    if not client.configured:
        preview = "\n".join(f"{i}. {t.name} — {t.artist}" for i, t in enumerate(ordered[:12], 1))
        more = "" if len(ordered) <= 12 else f"\n… +{len(ordered) - 12} faixas"
        return (
            "demo · ordem pronta, mas sem tokens não grava no Apple Music.\n"
            f"{preview}{more}"
        )
    name = (new_name or f"{playlist.name} · sequência").strip()
    created = client.create_library_playlist(
        name,
        ordered,
        description=f"Vivaldi · melhor sequência (origem: {playlist.name})",
    )
    return (
        f"✓ Criada no Apple Music: “{created.name}”\n"
        f"id {created.id} · {len(ordered)} faixas na nova ordem\n"
        "A playlist original permanece intacta (a API Apple não permite reordenar in-place)."
    )


def apply_filtered_playlist(
    client: AppleMusicClient,
    playlist: Playlist,
    tracks: list[Track],
    *,
    label: str,
) -> str:
    if not tracks:
        return "filtro sem faixas — nada a gravar"
    if not client.configured:
        return (
            f"demo · criaria “{playlist.name} · {label}” com {len(tracks)} faixa(s). "
            "Conecte tokens para gravar."
        )
    name = f"{playlist.name} · {label}".strip()
    created = client.create_library_playlist(
        name,
        tracks,
        description=f"Vivaldi · filtro {label} (origem: {playlist.name})",
    )
    return f"✓ Criada no Apple Music: “{created.name}” · {len(tracks)} faixas · id {created.id}"
