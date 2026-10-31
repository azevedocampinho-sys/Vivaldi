"""Partitura (ABC) + CIFRA helpers."""

from __future__ import annotations

import re
from pathlib import Path

from four_seasons.session import Layer, OUT_DIR, Project


def export_scores(project: Project) -> tuple[str, list[Path]]:
    """Write per-instrument CIFRA + ABC files. Returns summary + paths."""
    paths: list[Path] = []
    folder = OUT_DIR / f"{project.id}_scores"
    folder.mkdir(parents=True, exist_ok=True)
    lines = [f"Partituras · {project.title}", f"tom {project.key} {project.mode} · {project.tempo_bpm} BPM", "─" * 40]

    if not project.layers:
        lines.append("sem instrumentos — adicione camadas no Verão/Outono")
        return "\n".join(lines), paths

    for layer in project.layers:
        safe = re.sub(r"[^\w\-]+", "_", layer.instrument_name)[:32]
        cifra = layer.cifra.strip() or _fallback_cifra(project, layer)
        abc = layer.abc.strip() or _fallback_abc(project, layer)
        layer.cifra = cifra
        layer.abc = abc

        cifra_path = folder / f"{safe}_cifra.txt"
        abc_path = folder / f"{safe}_partitura.abc"
        cifra_path.write_text(cifra, encoding="utf-8")
        abc_path.write_text(abc, encoding="utf-8")
        paths.extend([cifra_path, abc_path])

        lines.append(f"\n▸ {layer.instrument_name}")
        lines.append(f"  CIFRA → {cifra_path.name}")
        lines.append(f"  PARTITURA (ABC) → {abc_path.name}")
        lines.append("  --- cifra ---")
        lines.append(cifra[:800])
        lines.append("  --- abc ---")
        lines.append(abc[:600])

    index = folder / "INDEX.txt"
    index.write_text("\n".join(lines), encoding="utf-8")
    paths.append(index)
    return "\n".join(lines), paths


def _fallback_cifra(project: Project, layer: Layer) -> str:
    chords = layer.chords or f"{project.key}  |  Am  |  F  |  G"
    return (
        f"{project.title} — {layer.instrument_name}\n"
        f"Tom: {project.key} {project.mode} · {project.tempo_bpm} BPM\n\n"
        f"[Verso]\n{chords}\n\n"
        f"[Refrão]\n{chords}\n\n"
        f"Notas: {layer.notes or '—'}\n"
    )


def _fallback_abc(project: Project, layer: Layer) -> str:
    root = project.key.replace("b", "_").replace("#", "^")[:2] or "C"
    return (
        f"X:1\nT:{project.title} — {layer.instrument_name}\n"
        f"M:4/4\nL:1/8\nQ:1/4={project.tempo_bpm}\n"
        f"K:{project.key}\n"
        f"|: {root}2 E2 G2 A2 | G2 E2 D2 C2 :|\n"
        f"% gerado pelo Vivaldi Four Seasons · edite no EasyABC / MuseScore\n"
    )
