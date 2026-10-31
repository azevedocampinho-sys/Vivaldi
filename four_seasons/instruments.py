"""Instrument catalog for Four Seasons layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    id: str
    name: str
    family: str
    role: str


INSTRUMENTS: list[Instrument] = [
    Instrument("vocals", "Voz / lead", "voz", "melodia"),
    Instrument("choir", "Backing vocals", "voz", "harmonia"),
    Instrument("piano", "Piano", "teclas", "harmonia"),
    Instrument("keys", "Synth / keys", "teclas", "textura"),
    Instrument("guitar_acoustic", "Violão", "cordas", "harmonia"),
    Instrument("guitar_electric", "Guitarra elétrica", "cordas", "riff"),
    Instrument("bass", "Baixo", "baixo", "groove"),
    Instrument("drums", "Bateria", "percussão", "groove"),
    Instrument("percussion", "Percussão", "percussão", "groove"),
    Instrument("strings", "Cordas (seção)", "cordas", "arranjo"),
    Instrument("violin", "Violino", "cordas", "melodia"),
    Instrument("cello", "Violoncelo", "cordas", "baixo"),
    Instrument("brass", "Metais", "sopro", "arranjo"),
    Instrument("sax", "Saxofone", "sopro", "melodia"),
    Instrument("flute", "Flauta", "sopro", "melodia"),
    Instrument("pad", "Pad atmosférico", "synth", "textura"),
    Instrument("fx", "FX / ambient", "synth", "textura"),
]

CHOICES = [(f"{i.name} · {i.family}", i.id) for i in INSTRUMENTS]
BY_ID = {i.id: i for i in INSTRUMENTS}


def label(instrument_id: str) -> str:
    inst = BY_ID.get(instrument_id)
    return inst.name if inst else instrument_id
