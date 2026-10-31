"""In-memory Four Seasons project."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "four_seasons_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEASONS = (
    ("spring", "Primavera", "Pré-produção"),
    ("summer", "Verão", "Produção"),
    ("autumn", "Outono", "Arranjo"),
    ("winter", "Inverno", "Pós-produção"),
)


@dataclass
class Layer:
    id: str
    instrument_id: str
    instrument_name: str
    notes: str = ""
    chords: str = ""
    muted: bool = False
    gain_db: float = 0.0
    abc: str = ""
    cifra: str = ""


@dataclass
class Project:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    title: str = "Sem título"
    concept: str = ""
    mood: str = ""
    tempo_bpm: int = 100
    key: str = "C"
    mode: str = "maior"
    season: str = "spring"
    reference_summary: str = ""
    reference_tracks: list[dict[str, Any]] = field(default_factory=list)
    humming_notes: str = ""
    humming_path: str | None = None
    structure: str = ""
    layers: list[Layer] = field(default_factory=list)
    chat_log: list[tuple[str, str]] = field(default_factory=list)
    mix_notes: str = ""
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def layers_blob(self) -> str:
        if not self.layers:
            return "(nenhum instrumento ainda — adicione com +)"
        rows = []
        for i, layer in enumerate(self.layers, 1):
            flag = "🔇" if layer.muted else "●"
            rows.append(
                f"{i}. {flag} {layer.instrument_name}  gain {layer.gain_db:+.0f} dB\n"
                f"   notas: {layer.notes or '—'}\n"
                f"   acordes: {layer.chords or '—'}"
            )
        return "\n".join(rows)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self) -> Path:
        self.touch()
        path = OUT_DIR / f"{self.id}_{_slug(self.title)}.json"
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path


def _slug(text: str) -> str:
    keep = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower())
    return (keep[:40] or "projeto").strip("-")


def project_from_dict(data: dict[str, Any]) -> Project:
    layers = [Layer(**layer) for layer in data.get("layers") or []]
    payload = {k: v for k, v in data.items() if k != "layers"}
    payload["layers"] = layers
    payload["chat_log"] = [tuple(x) for x in payload.get("chat_log") or []]
    return Project(**payload)
