"""Extrator local seguro — zip, tar (+ gz/bz2/xz) e .gz simples."""

from __future__ import annotations

import gzip
import shutil
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "zip_out"

SUPPORTED_LABEL = ".zip · .tar · .tar.gz · .tgz · .tar.bz2 · .tar.xz · .gz"

_TAR_SUFFIXES = (
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.bz2",
    ".tbz2",
    ".tar.xz",
    ".txz",
)


def _is_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _safe_join(dest: Path, name: str) -> Path:
    # normaliza separadores do zip (sempre /)
    clean = name.replace("\\", "/").lstrip("/")
    target = (dest / clean).resolve()
    if not _is_within(dest, target):
        raise ValueError(f"caminho inseguro no arquivo: {name}")
    return target


def _unique_dir(base: Path, stem: str) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    candidate = base / stem
    if not candidate.exists():
        return candidate
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return base / f"{stem}-{stamp}"


def _list_tree(root: Path, *, limit: int = 400) -> list[str]:
    if not root.exists():
        return []
    lines: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root)
            size = path.stat().st_size
            lines.append(f"{rel}  ({_fmt_size(size)})")
            if len(lines) >= limit:
                lines.append("… (lista truncada)")
                break
    return lines


def _fmt_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.0f} {u}" if u == "B" else f"{size:.1f} {u}"
        size /= 1024
    return f"{n} B"


def _kind(path: Path) -> str:
    name = path.name.lower()
    for suf in _TAR_SUFFIXES:
        if name.endswith(suf):
            return "tar"
    if name.endswith(".zip"):
        return "zip"
    if name.endswith(".gz") and not name.endswith(".tar.gz"):
        return "gz"
    # sniff
    if zipfile.is_zipfile(path):
        return "zip"
    if tarfile.is_tarfile(path):
        return "tar"
    return "unknown"


def _extract_zip(src: Path, dest: Path) -> tuple[int, list[str]]:
    count = 0
    skipped: list[str] = []
    with zipfile.ZipFile(src, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if not name:
                continue
            try:
                if name.endswith("/"):
                    _safe_join(dest, name.rstrip("/")).mkdir(parents=True, exist_ok=True)
                    continue
                target = _safe_join(dest, name)
            except ValueError as exc:
                skipped.append(str(exc))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src_f, open(target, "wb") as out_f:
                shutil.copyfileobj(src_f, out_f)
            count += 1
    return count, skipped


def _extract_tar(src: Path, dest: Path) -> tuple[int, list[str]]:
    count = 0
    skipped: list[str] = []
    with tarfile.open(src, "r:*") as tf:
        for member in tf.getmembers():
            name = member.name
            if not name:
                continue
            try:
                target = _safe_join(dest, name)
            except ValueError as exc:
                skipped.append(str(exc))
                continue
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() and not member.isreg():
                skipped.append(f"ignorado (não-arquivo): {name}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted = tf.extractfile(member)
            if extracted is None:
                continue
            with extracted, open(target, "wb") as out_f:
                shutil.copyfileobj(extracted, out_f)
            count += 1
    return count, skipped


def _extract_gz(src: Path, dest: Path) -> tuple[int, list[str]]:
    dest.mkdir(parents=True, exist_ok=True)
    out_name = src.name[:-3] if src.name.lower().endswith(".gz") else src.stem
    target = _safe_join(dest, out_name)
    with gzip.open(src, "rb") as src_f, open(target, "wb") as out_f:
        shutil.copyfileobj(src_f, out_f)
    return 1, []


def unpack(archive_path: str | None, out_dir: str | None = None) -> tuple[str, str]:
    """Descompacta para uma subpasta em out_dir. Retorna (log, lista de arquivos)."""
    if not archive_path:
        return "anexe um arquivo compactado (.zip, .tar.gz, …)", ""

    src = Path(archive_path).expanduser()
    if not src.is_file():
        return f"arquivo não encontrado: {src}", ""

    base_out = Path(out_dir or DEFAULT_OUT).expanduser()
    dest = _unique_dir(base_out, src.stem.replace(".tar", ""))
    dest.mkdir(parents=True, exist_ok=True)

    kind = _kind(src)
    log_lines = [
        f"arquivo  {src.name}",
        f"tipo     {kind}",
        f"destino  {dest}",
        "────────────────────────",
    ]
    try:
        if kind == "zip":
            n, skipped = _extract_zip(src, dest)
        elif kind == "tar":
            n, skipped = _extract_tar(src, dest)
        elif kind == "gz":
            n, skipped = _extract_gz(src, dest)
        else:
            shutil.rmtree(dest, ignore_errors=True)
            return (
                f"formato não suportado: {src.suffix or src.name}\n"
                f"use {SUPPORTED_LABEL}",
                "",
            )
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(dest, ignore_errors=True)
        return f"falha ao descompactar: {exc}", ""

    files = _list_tree(dest)
    log_lines.append(f"ok · {n} arquivo(s) extraído(s)")
    for note in skipped[:12]:
        log_lines.append(f"⚠ {note}")
    if len(skipped) > 12:
        log_lines.append(f"⚠ … +{len(skipped) - 12} ignorado(s)")
    log_lines.append(f"pasta · {dest}")
    listing = "\n".join(files) if files else "(vazio)"
    return "\n".join(log_lines), listing
