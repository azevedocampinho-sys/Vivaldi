"""Diálogos nativos do Finder (osascript) — só faz sentido no Mac local."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path


def _osascript(source: str) -> tuple[bool, str]:
    if platform.system() != "Darwin":
        return False, "seleção pelo Finder só funciona no macOS"
    try:
        proc = subprocess.run(
            ["osascript", "-e", source],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"falha ao abrir o Finder: {exc}"
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        if "User canceled" in err or "(-128)" in err or not out:
            return False, ""
        return False, err or "seleção cancelada"
    return True, out


def _escape_as(path: str) -> str:
    return path.replace("\\", "\\\\").replace('"', '\\"')


def pick_file(prompt: str = "Escolha o arquivo compactado") -> str:
    """Compat: um arquivo (primeira seleção)."""
    files = pick_files(prompt)
    return files.splitlines()[0] if files else ""


def pick_files(prompt: str = "Escolha os arquivos compactados") -> str:
    """Retorna caminhos POSIX, um por linha (múltipla seleção no Finder)."""
    script = (
        f'set theFiles to choose file with prompt "{prompt}" with multiple selections allowed\n'
        "set out to \"\"\n"
        "repeat with f in theFiles\n"
        "  set out to out & POSIX path of f & linefeed\n"
        "end repeat\n"
        "return out"
    )
    ok, value = _osascript(script)
    if not ok:
        return ""
    lines = [ln.strip() for ln in value.splitlines() if ln.strip()]
    return "\n".join(lines)


def pick_folder(prompt: str = "Escolha a pasta de saída") -> str:
    ok, value = _osascript(
        f'set f to choose folder with prompt "{prompt}"\n'
        "return POSIX path of f"
    )
    if not ok:
        return ""
    return value.rstrip("/") or value


def move_to_trash(path: str | Path) -> tuple[bool, str]:
    """Envia ao Lixo do macOS via Finder (recuperável)."""
    target = Path(path).expanduser()
    if not target.exists():
        return False, f"não encontrado para lixeira: {target}"
    if platform.system() != "Darwin":
        try:
            target.unlink()
            return True, f"apagado (sem Lixeira neste SO): {target.name}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    posix = _escape_as(str(target.resolve()))
    # Finder "delete" = move para o Lixo
    ok, msg = _osascript(
        f'tell application "Finder" to delete (POSIX file "{posix}" as alias)'
    )
    if ok:
        return True, f"lixeira · {target.name}"

    # fallback: mv para ~/.Trash
    trash = Path.home() / ".Trash"
    try:
        trash.mkdir(exist_ok=True)
        dest = trash / target.name
        if dest.exists():
            stem, suf = target.stem, target.suffix
            i = 1
            while dest.exists():
                dest = trash / f"{stem} {i}{suf}"
                i += 1
        target.rename(dest)
        return True, f"lixeira · {target.name}"
    except Exception as exc:  # noqa: BLE001
        return False, msg or f"falha ao mover para o Lixo: {exc}"
