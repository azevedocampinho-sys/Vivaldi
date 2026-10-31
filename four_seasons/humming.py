"""Analyze hummed / sung takes for Four Seasons (local, no cloud)."""

from __future__ import annotations

import math
import wave
from pathlib import Path


def analyze_humming(path: str | None) -> str:
    if not path:
        return "grave ou envie um cantarolar para analisar"
    p = Path(path)
    if not p.exists():
        return f"arquivo não encontrado: {path}"

    # Prefer wav analysis; otherwise report metadata only
    suffix = p.suffix.lower()
    if suffix == ".wav":
        try:
            return _analyze_wav(p)
        except Exception as exc:  # noqa: BLE001
            return f"áudio recebido ({p.name}) · análise básica falhou: {exc}"

    size_kb = p.stat().st_size / 1024
    return (
        f"cantarolar recebido: {p.name} ({size_kb:.0f} KB, {suffix or 'sem extensão'})\n"
        "A IA usará este take como referência melódica na produção. "
        "Dica: exporte WAV mono 16-bit para análise de pitch local mais rica."
    )


def _analyze_wav(path: Path) -> str:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        rate = wf.getframerate()
        frames = wf.getnframes()
        width = wf.getsampwidth()
        duration = frames / float(rate or 1)
        raw = wf.readframes(min(frames, rate * 20))  # até 20s

    if width != 2:
        return (
            f"WAV {path.name}: {duration:.1f}s · {rate} Hz · {channels} ch\n"
            "Converta para PCM 16-bit para estimar tom fundamental."
        )

    # Mono mix of int16 samples
    import array

    samples = array.array("h")
    samples.frombytes(raw)
    if channels > 1:
        mono = [
            sum(samples[i : i + channels]) // channels
            for i in range(0, len(samples) - channels + 1, channels)
        ]
    else:
        mono = list(samples)

    if len(mono) < rate // 4:
        return f"WAV muito curto ({duration:.2f}s) — cante pelo menos ~1s."

    # Rough pitch via autocorrelation on a mid window
    start = len(mono) // 4
    window = mono[start : start + min(len(mono) // 2, rate * 2)]
    pitch_hz = _estimate_pitch_hz(window, rate)
    note = _hz_to_note(pitch_hz) if pitch_hz else "?"
    rms = math.sqrt(sum(s * s for s in window) / max(len(window), 1))
    energy = "suave" if rms < 800 else ("média" if rms < 2500 else "intensa")

    return (
        f"cantarolar: {path.name}\n"
        f"duração {duration:.1f}s · {rate} Hz · {channels} ch\n"
        f"tom estimado ≈ {pitch_hz:.1f} Hz ({note}) · energia {energy}\n"
        "Use isto como seed melódico na Primavera/Verão; a IA local amarra aos seus "
        "referenciais Apple Music."
    )


def _estimate_pitch_hz(samples: list[int], rate: int) -> float | None:
    n = len(samples)
    if n < 256:
        return None
    # Normalize
    mean = sum(samples) / n
    x = [s - mean for s in samples]
    # Autocorr for periods corresponding to 80–500 Hz
    min_lag = max(1, int(rate / 500))
    max_lag = min(n // 2, int(rate / 80))
    best_lag = None
    best_val = 0.0
    for lag in range(min_lag, max_lag):
        acc = 0.0
        for i in range(0, n - lag, 4):  # stride for speed
            acc += x[i] * x[i + lag]
        if acc > best_val:
            best_val = acc
            best_lag = lag
    if not best_lag or best_val <= 0:
        return None
    return rate / float(best_lag)


def _hz_to_note(hz: float) -> str:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    midi = int(round(69 + 12 * math.log2(hz / 440.0)))
    return f"{names[midi % 12]}{midi // 12 - 1}"
