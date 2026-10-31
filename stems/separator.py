"""Separação local de stems via Demucs / HTDemucs (voz, baixo, bateria, outros)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import gradio as gr

from ui.theme import progress_html

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "stems_out"
DEFAULT_OUT.mkdir(parents=True, exist_ok=True)

MODELS = [
    "htdemucs",       # Hybrid Transformer — padrão sólido
    "htdemucs_ft",    # fine-tuned (melhor qualidade, mais lento)
    "htdemucs_6s",    # 6 stems (inclui piano/guitar quando disponível)
    "mdx_extra",      # alternativa MDX
]

MODES = [
    "Instrumental rápido (voz + instrumental)",
    "Stems completos (voz, baixo, bateria, outros)",
]


def demucs_available() -> bool:
    try:
        import demucs  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def status_line() -> str:
    if demucs_available():
        try:
            import torch

            device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
            return f"Demucs pronto · device preferido: {device}"
        except Exception:  # noqa: BLE001
            return "Demucs instalado"
    return (
        "Demucs não instalado · no venv: pip install demucs torch torchaudio "
        "(primeira execução baixa os pesos do modelo)"
    )


def _pick_device() -> str:
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


def _collect_outputs(out_root: Path, track_stem: str, model: str) -> list[Path]:
    """Demucs grava em out_root/model/track_stem/*.wav"""
    folder = out_root / model / track_stem
    if not folder.is_dir():
        # procura qualquer pasta recente com o nome da faixa
        hits = sorted(out_root.rglob(f"*/{track_stem}/*.wav"))
        return hits
    return sorted(folder.glob("*.wav"))


def separate(
    audio_path: str | None,
    model: str,
    mode: str,
    out_dir_str: str,
    shifts: int = 1,
):
    """Generator Gradio: log, files_info, progress_html, button update."""
    busy = gr.update(value="Separando…", interactive=False, elem_classes=["batch-cta", "is-running"])
    idle = gr.update(value="Separar stems", interactive=True, elem_classes=["batch-cta"])

    def pack(log: str, files: str, frac: float, label: str, *, running: bool, done: bool = False):
        return (
            log,
            files,
            progress_html(frac, label, running=running, done=done),
            busy if running and not done else idle,
        )

    if not demucs_available():
        yield pack(
            "erro · demucs/torch não instalados\n"
            "  source .venv/bin/activate\n"
            "  pip install demucs torch torchaudio",
            "",
            0,
            "erro",
            running=False,
        )
        return

    if not audio_path:
        yield pack("erro · envie um áudio (wav, mp3, m4a, flac…)", "", 0, "erro", running=False)
        return

    src = Path(audio_path)
    if not src.is_file():
        yield pack(f"erro · arquivo inválido: {audio_path}", "", 0, "erro", running=False)
        return

    model = (model or "htdemucs").strip()
    out_dir = Path((out_dir_str or str(DEFAULT_OUT)).strip()).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    two_stems = mode.startswith("Instrumental")
    device = _pick_device()
    # MPS às vezes falha em ops do demucs — fallback automático via CPU se necessário
    def build_cmd(dev: str) -> list[str]:
        c = [
            sys.executable,
            "-m",
            "demucs.separate",
            "-n",
            model,
            "-o",
            str(out_dir),
            "-d",
            dev,
            "--shifts",
            str(max(0, int(shifts or 0))),
        ]
        if two_stems:
            c.extend(["--two-stems", "vocals"])
        c.append(str(src))
        return c

    cmd = build_cmd(device)

    lines = [
        f"fonte   {src.name}",
        f"modelo  {model}",
        f"modo    {'instrumental (2 stems)' if two_stems else '4 stems'}",
        f"device  {device}",
        f"saída   {out_dir}",
        "─" * 44,
        "iniciando demucs… (1ª vez baixa pesos)",
    ]
    yield pack("\n".join(lines), "aguardando…", 0.05, "preparando…", running=True)

    t0 = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    # progresso estimado por tempo (demucs não dá % estável)
    pulse = 0.08
    for line in proc.stdout:
        text = line.rstrip()
        if text:
            lines.append(text[-200:])
            if len(lines) > 80:
                lines = lines[:6] + ["…"] + lines[-60:]
        pulse = min(0.92, pulse + 0.01)
        elapsed = int(time.time() - t0)
        yield pack(
            "\n".join(lines),
            "processando…",
            pulse,
            f"separando · {elapsed}s",
            running=True,
        )

    code = proc.wait()
    elapsed = int(time.time() - t0)

    if code != 0 and device != "cpu":
        lines.append(f"falha no device {device} (exit {code}) · tentando CPU…")
        yield pack("\n".join(lines), "retry cpu…", 0.2, "retry CPU", running=True)
        proc2 = subprocess.Popen(
            build_cmd("cpu"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc2.stdout is not None
        for line in proc2.stdout:
            text = line.rstrip()
            if text:
                lines.append(text[-200:])
            pulse = min(0.92, pulse + 0.01)
            yield pack("\n".join(lines), "processando (cpu)…", pulse, "separando · cpu", running=True)
        code = proc2.wait()
        device = "cpu"
        elapsed = int(time.time() - t0)

    if code != 0:
        lines.append(f"erro · demucs exit {code}")
        yield pack("\n".join(lines), "", 1.0, "erro", running=False, done=False)
        return

    track_stem = src.stem
    files = _collect_outputs(out_dir, track_stem, model)
    if not files:
        lines.append("aviso · processo ok, mas arquivos não encontrados — confira a pasta de saída")
        yield pack("\n".join(lines), str(out_dir), 1.0, "concluído?", running=False, done=True)
        return

    # copia instrumental com nome amigável se existir no_vocals
    friendly: list[str] = []
    for f in files:
        friendly.append(str(f))
        if f.name.lower().startswith("no_vocals"):
            dest = f.parent / f"{track_stem}__instrumental{f.suffix}"
            if not dest.exists():
                shutil.copy2(f, dest)
                friendly.append(str(dest))

    lines.append("─" * 44)
    lines.append(f"feito · {len(files)} stem(s) · {elapsed}s · device {device}")
    for f in files:
        lines.append(f"  · {f.name}  ({f.stat().st_size // 1024} KB)")

    listing = "\n".join(friendly)
    yield pack("\n".join(lines), listing, 1.0, f"concluído · {len(files)} arquivos", running=False, done=True)
