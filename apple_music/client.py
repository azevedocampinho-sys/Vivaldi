"""Official Apple Music API client with caching + gentle rate limits (anti-ban)."""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

API = "https://api.music.apple.com/v1"
CACHE_DIR = ROOT / ".cache" / "apple_music"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Conservative pacing — personal app, not a scraper farm
MIN_INTERVAL_SEC = 0.35
MAX_RETRIES = 5


@dataclass
class Track:
    id: str
    name: str
    artist: str
    album: str
    year: int | None
    genre: str
    duration_ms: int | None
    isrc: str | None = None
    catalog_id: str | None = None
    resource_type: str = "library-songs"


@dataclass
class Playlist:
    id: str
    name: str
    tracks: list[Track]
    can_edit: bool = False


class RateLimiter:
    def __init__(self, min_interval: float = MIN_INTERVAL_SEC) -> None:
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self.min_interval - (now - self._last)
            if delay > 0:
                time.sleep(delay)
            self._last = time.monotonic()


class AppleMusicClient:
    """Read/write only via api.music.apple.com. No scraping, no downloads."""

    def __init__(
        self,
        developer_token: str | None = None,
        user_token: str | None = None,
        storefront: str = "br",
    ) -> None:
        self.developer_token = (developer_token or os.getenv("APPLE_MUSIC_DEVELOPER_TOKEN") or "").strip()
        self.user_token = (user_token or os.getenv("APPLE_MUSIC_USER_TOKEN") or "").strip()
        self.storefront = (storefront or os.getenv("APPLE_MUSIC_STOREFRONT") or "br").strip()
        self._limiter = RateLimiter()
        self._http = httpx.Client(timeout=30.0)

    @property
    def configured(self) -> bool:
        return bool(self.developer_token and self.user_token)

    def status_line(self) -> str:
        if self.configured:
            return "conectado · API oficial Apple Music (tokens locais)"
        return "modo demo · sem tokens — use sample_data (zero risco de ban)"

    def _headers(self) -> dict[str, str]:
        if not self.developer_token:
            raise RuntimeError("APPLE_MUSIC_DEVELOPER_TOKEN ausente")
        h = {
            "Authorization": f"Bearer {self.developer_token}",
            "Accept": "application/json",
        }
        if self.user_token:
            h["Music-User-Token"] = self.user_token
        return h

    def _request(
        self,
        method: str,
        path: str,
        *,
        allow_empty: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{API}{path}"
        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES):
            self._limiter.wait()
            try:
                resp = self._http.request(method, url, headers=self._headers(), **kwargs)
            except httpx.HTTPError as exc:
                last_err = exc
                time.sleep(0.6 * (2**attempt))
                continue

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(min(max(retry_after, 1.0), 60.0))
                continue
            if resp.status_code >= 500:
                time.sleep(0.8 * (2**attempt))
                continue
            if resp.status_code >= 400:
                raise RuntimeError(f"Apple Music API {resp.status_code}: {resp.text[:400]}")
            if allow_empty and resp.status_code in (200, 201, 204) and not (resp.content or b"").strip():
                return {}
            if not (resp.content or b"").strip():
                return {}
            return resp.json()
        raise RuntimeError(f"Falha após retries: {last_err}")

    def invalidate_playlist_cache(self, playlist_id: str | None = None) -> None:
        for path in CACHE_DIR.glob("*.json"):
            name = path.name
            wipe = playlist_id is None or name == "library_playlists.json" or (
                playlist_id is not None and playlist_id in name
            )
            if wipe:
                try:
                    path.unlink()
                except OSError:
                    pass

    @staticmethod
    def track_ref(track: Track) -> dict[str, str]:
        """Prefer catalog song id when available — more reliable for playlist writes."""
        if track.catalog_id:
            return {"id": track.catalog_id, "type": "songs"}
        rtype = track.resource_type or "library-songs"
        if rtype in {"library-songs", "library-music-videos", "songs", "music-videos"}:
            return {"id": track.id, "type": rtype}
        return {"id": track.id, "type": "library-songs"}

    def _cache_path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
        return CACHE_DIR / f"{safe}.json"

    def _read_cache(self, key: str, max_age_sec: int = 300) -> dict | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        if time.time() - path.stat().st_mtime > max_age_sec:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None

    def _write_cache(self, key: str, data: dict) -> None:
        self._cache_path(key).write_text(json.dumps(data), encoding="utf-8")

    def list_library_playlists(self) -> list[tuple[str, str]]:
        """Returns [(label, id), ...]."""
        cache_key = "library_playlists"
        cached = self._read_cache(cache_key, max_age_sec=180)
        items: list[dict] = []
        if cached:
            items = cached.get("data", [])
        else:
            offset = 0
            while True:
                data = self._request(
                    "GET",
                    "/me/library/playlists",
                    params={"limit": 25, "offset": offset},
                )
                chunk = data.get("data") or []
                items.extend(chunk)
                next_url = (data.get("next") or "").strip()
                if not chunk or not next_url:
                    break
                offset += len(chunk)
                if offset > 500:  # hard safety cap
                    break
            self._write_cache(cache_key, {"data": items})

        out: list[tuple[str, str]] = []
        for it in items:
            attrs = it.get("attributes") or {}
            name = attrs.get("name") or it.get("id")
            out.append((f"{name}", it["id"]))
        return out

    def get_library_playlist_tracks(self, playlist_id: str) -> Playlist:
        cache_key = f"playlist_{playlist_id}"
        cached = self._read_cache(cache_key, max_age_sec=120)
        tracks: list[Track] = []
        name = playlist_id

        if cached:
            return Playlist(
                id=playlist_id,
                name=cached.get("name", playlist_id),
                tracks=[Track(**t) for t in cached.get("tracks", [])],
                can_edit=bool(cached.get("can_edit")),
            )

        meta = self._request("GET", f"/me/library/playlists/{playlist_id}")
        can_edit = False
        if meta.get("data"):
            attrs0 = meta["data"][0].get("attributes") or {}
            name = attrs0.get("name") or name
            can_edit = bool(attrs0.get("canEdit"))

        offset = 0
        while True:
            data = self._request(
                "GET",
                f"/me/library/playlists/{playlist_id}/tracks",
                params={"limit": 100, "offset": offset},
            )
            chunk = data.get("data") or []
            for song in chunk:
                attrs = song.get("attributes") or {}
                arts = attrs.get("artistName") or ""
                album = attrs.get("albumName") or ""
                year = None
                release = attrs.get("releaseDate") or ""
                if release and len(release) >= 4 and release[:4].isdigit():
                    year = int(release[:4])
                genres = attrs.get("genreNames") or []
                tracks.append(
                    Track(
                        id=song.get("id") or "",
                        name=attrs.get("name") or "?",
                        artist=arts,
                        album=album,
                        year=year,
                        genre=(genres[0] if genres else "—"),
                        duration_ms=attrs.get("durationInMillis"),
                        isrc=attrs.get("isrc"),
                        catalog_id=(attrs.get("playParams") or {}).get("catalogId"),
                        resource_type=song.get("type") or "library-songs",
                    )
                )
            if len(chunk) < 100:
                break
            offset += len(chunk)
            if offset > 2000:
                break

        payload = {
            "name": name,
            "can_edit": can_edit,
            "tracks": [t.__dict__ for t in tracks],
        }
        self._write_cache(cache_key, payload)
        return Playlist(id=playlist_id, name=name, tracks=tracks, can_edit=can_edit)

    def create_library_playlist(
        self,
        name: str,
        tracks: list[Track],
        *,
        description: str | None = None,
    ) -> Playlist:
        """Create a library playlist and fill it with tracks (official write path)."""
        if not self.configured:
            raise RuntimeError("Tokens Apple Music necessários para escrever na biblioteca")
        if not name.strip():
            raise RuntimeError("Nome da playlist vazio")
        if not tracks:
            raise RuntimeError("Nenhuma faixa para gravar")

        refs = [self.track_ref(t) for t in tracks if t.id or t.catalog_id]
        if not refs:
            raise RuntimeError("Faixas sem id válido para a API Apple Music")

        # Apple aceita tracks no create; lotes grandes → create + POST /tracks
        first_batch = refs[:100]
        rest = refs[100:]
        attributes: dict[str, Any] = {"name": name.strip(), "isPublic": False}
        if description:
            # Apple accepts plain string or editorial {standard}; string is widely used.
            attributes["description"] = description.strip()[:200]
        body: dict[str, Any] = {
            "attributes": attributes,
            "relationships": {"tracks": {"data": first_batch}},
        }
        created = self._request("POST", "/me/library/playlists", json=body)
        data = (created.get("data") or [None])[0]
        if not data or not data.get("id"):
            raise RuntimeError("Apple Music não retornou id da playlist criada")
        new_id = data["id"]
        new_name = ((data.get("attributes") or {}).get("name")) or name

        for i in range(0, len(rest), 100):
            chunk = rest[i : i + 100]
            self._request(
                "POST",
                f"/me/library/playlists/{new_id}/tracks",
                json={"data": chunk},
                allow_empty=True,
            )

        self.invalidate_playlist_cache()
        return Playlist(id=new_id, name=new_name, tracks=list(tracks), can_edit=True)

    def try_remove_tracks(self, playlist_id: str, track_ids: list[str]) -> tuple[bool, str]:
        """Best-effort DELETE. Official MusicKit tokens usually get 403 — report honestly."""
        if not track_ids:
            return True, "nada a remover"
        # Documented public API historically rejected DELETE; try once and surface result.
        try:
            self._request(
                "DELETE",
                f"/me/library/playlists/{playlist_id}/tracks",
                json={"data": [{"id": tid, "type": "library-songs"} for tid in track_ids]},
                allow_empty=True,
            )
            self.invalidate_playlist_cache(playlist_id)
            return True, f"removidas {len(track_ids)} faixa(s) da playlist original"
        except RuntimeError as exc:
            msg = str(exc)
            if "401" in msg or "403" in msg or "405" in msg:
                return (
                    False,
                    "A API oficial da Apple bloqueia apagar faixas da playlist original "
                    "(403/401). Use criar playlist limpa — é o caminho suportado.",
                )
            return False, msg
