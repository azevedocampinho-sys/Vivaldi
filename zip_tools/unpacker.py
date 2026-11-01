"""Extrator local seguro — zip, 7z, tar (+ gz/bz2/xz) e .gz simples."""

from __future__ import annotations

import gzip
import shutil
import subprocess
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "zip_out"

SUPPORTED_LABEL = ".zip · .7z · .tar · .tar.gz · .tgz · .tar.bz2 · .tar.xz · .gz"

_7Z_MAGIC = b"7z\xbc\xaf'\x1c"

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


def _read_head(path: Path, n: int = 4096) -> bytes:
    with open(path, "rb") as f:
        return f.read(n)


def _kind(path: Path) -> str:
    name = path.name.lower()
    head = _read_head(path, 16)
    if head.startswith(_7Z_MAGIC):
        return "7z"
    if name.endswith(".7z"):
        return "broken-7z" if head == b"\x00" * len(head) else "7z"
    if head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06") or head.startswith(b"PK\x07\x08"):
        return "zip"
    if head.startswith(b"\x1f\x8b"):
        # gzip — pode ser .tar.gz
        if any(name.endswith(s) for s in (".tar.gz", ".tgz")):
            return "tar"
        return "gz"
    if head.startswith(b"BZh") or head.startswith(b"\xfd7zXZ"):
        return "tar"
    for suf in _TAR_SUFFIXES:
        if name.endswith(suf):
            return "tar"
    if name.endswith(".zip"):
        # extensão zip mas header estranho — ainda tenta se is_zipfile
        if zipfile.is_zipfile(path):
            return "zip"
        return "broken-zip"
    if name.endswith(".gz") and not name.endswith(".tar.gz"):
        return "gz"
    if zipfile.is_zipfile(path):
        return "zip"
    if tarfile.is_tarfile(path):
        return "tar"
    return "unknown"


def _nonzero_ratio(path: Path, offset: int, n: int = 1024 * 1024) -> float:
    size = path.stat().st_size
    if size <= 0:
        return 0.0
    offset = max(0, min(offset, max(0, size - 1)))
    with open(path, "rb") as f:
        f.seek(offset)
        chunk = f.read(min(n, size - offset))
    if not chunk:
        return 0.0
    return sum(1 for b in chunk if b) / len(chunk)


def _diagnose_before(src: Path, kind: str) -> str | None:
    """Mensagem de erro cedo, ou None se parece ok para tentar."""
    size = src.stat().st_size
    if size == 0:
        return "arquivo vazio (0 bytes)"
    head = _read_head(src, 4096)
    if head and head == b"\x00" * len(head):
        # ZIP “fantasma”: diretório central no fim, mas o conteúdo não baixou
        inner = ""
        try:
            if zipfile.is_zipfile(src):
                with zipfile.ZipFile(src, "r") as zf:
                    names = [i.filename for i in zf.infolist()[:5]]
                    if names:
                        inner = "conteúdo declarado: " + ", ".join(names)
                        if len(zf.infolist()) > 5:
                            inner += f" (+{len(zf.infolist()) - 5})"
                        inner += "\n"
        except Exception:  # noqa: BLE001
            pass
        r0 = _nonzero_ratio(src, 0)
        r50 = _nonzero_ratio(src, size // 2)
        r75 = _nonzero_ratio(src, (size * 3) // 4)
        return (
            "este arquivo no disco está incompleto/corrompido — não é culpa do Vivaldi.\n"
            f"{inner}"
            f"amostra de dados: início {r0:.0%} · meio {r50:.0%} · 75% {r75:.0%} preenchidos.\n"
            "O fim do ZIP existe (lista de arquivos), mas o começo está zerado "
            "(download/torrent não terminou).\n"
            "Apague e baixe de novo o arquivo original, depois use 📁 Arquivo… no Finder "
            "(não o upload do browser — ele só copia o mesmo arquivo quebrado)."
        )
    if kind == "broken-zip":
        return (
            f"extensão .zip, mas o cabeçalho não é PK ({head[:8]!r}).\n"
            "Pode ser ISO/7z/RAR renomeado, ou download incompleto."
        )
    if kind == "broken-7z":
        return (
            "extensão .7z, mas o arquivo começa zerado — download incompleto/corrompido."
        )
    if kind == "zip" and size < 200_000_000:
        # testzip lê o arquivo inteiro — só em ZIPs pequenos
        try:
            with zipfile.ZipFile(src, "r") as zf:
                bad = zf.testzip()
                if bad is not None:
                    return (
                        f"ZIP corrompido ou incompleto (falhou em: {bad}).\n"
                        "Bad magic number costuma significar bytes faltando no meio do arquivo."
                    )
        except zipfile.BadZipFile as exc:
            return f"ZIP inválido: {exc}"
        except Exception as exc:  # noqa: BLE001
            return f"não foi possível validar o ZIP: {exc}"
    return None


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


def _extract_zip_ditto(src: Path, dest: Path) -> tuple[int, list[str]]:
    """Fallback macOS para ZIPs grandes / ZIP64 problemáticos."""
    dest.mkdir(parents=True, exist_ok=True)
    ditto = shutil.which("ditto")
    if not ditto:
        raise RuntimeError("ditto não encontrado")
    proc = subprocess.run(
        [ditto, "-x", "-k", "--sequesterRsrc", "--", str(src), str(dest)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "ditto falhou").strip()
        raise RuntimeError(err)
    files = [p for p in dest.rglob("*") if p.is_file()]
    return len(files), []


def _extract_7z(src: Path, dest: Path) -> tuple[int, list[str]]:
    """Extrai .7z via py7zr (com fallback para CLI 7z/7zz)."""
    dest.mkdir(parents=True, exist_ok=True)
    skipped: list[str] = []

    try:
        import py7zr
    except ImportError:
        return _extract_7z_cli(src, dest)

    with py7zr.SevenZipFile(src, mode="r") as archive:
        names = archive.getnames()
        safe: list[str] = []
        for name in names:
            if not name or name.endswith("/"):
                # pastas — valida e deixa o extract criar
                try:
                    if name:
                        _safe_join(dest, name.rstrip("/"))
                    safe.append(name)
                except ValueError as exc:
                    skipped.append(str(exc))
                continue
            try:
                _safe_join(dest, name)
                safe.append(name)
            except ValueError as exc:
                skipped.append(str(exc))
        if not safe and names:
            raise RuntimeError("nenhum caminho seguro no .7z")
        archive.extract(path=str(dest), targets=safe or None)

    files = [p for p in dest.rglob("*") if p.is_file()]
    return len(files), skipped


def _extract_7z_cli(src: Path, dest: Path) -> tuple[int, list[str]]:
    dest.mkdir(parents=True, exist_ok=True)
    exe = shutil.which("7zz") or shutil.which("7z") or shutil.which("7za")
    if not exe:
        raise RuntimeError(
            "py7zr não instalado e CLI 7z não encontrada. "
            "Rode: pip install py7zr  (ou brew install p7zip)"
        )
    proc = subprocess.run(
        [exe, "x", f"-o{dest}", "-y", "--", str(src)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "7z falhou").strip()
        raise RuntimeError(err)
    # valida path traversal pós-extração
    skipped: list[str] = []
    base = dest.resolve()
    for path in list(dest.rglob("*")):
        try:
            path.resolve().relative_to(base)
        except ValueError:
            skipped.append(f"removido path inseguro: {path}")
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
    files = [p for p in dest.rglob("*") if p.is_file()]
    return len(files), skipped


def _collect_sources(
    archive_upload: str | list[str] | None,
    archive_path: str | None,
) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        key = str(p.expanduser().resolve()) if p.exists() else str(p.expanduser())
        if key in seen:
            return
        seen.add(key)
        found.append(p.expanduser())

    for line in (archive_path or "").splitlines():
        line = line.strip().strip('"').strip("'")
        if line:
            add(Path(line))

    if archive_upload:
        items = archive_upload if isinstance(archive_upload, (list, tuple)) else [archive_upload]
        for item in items:
            if item:
                add(Path(str(item)))

    return found


def _unpack_one(src: Path, base_out: Path) -> tuple[bool, str, str]:
    """Descompacta um arquivo. Retorna (ok, log, listing)."""
    if not src.is_file():
        return False, f"arquivo não encontrado: {src}", ""

    dest = _unique_dir(base_out, src.stem.replace(".tar", ""))
    dest.mkdir(parents=True, exist_ok=True)

    kind = _kind(src)
    size = src.stat().st_size
    log_lines = [
        f"arquivo  {src}",
        f"tamanho  {_fmt_size(size)}",
        f"tipo     {kind}",
        f"destino  {dest}",
        "────────────────────────",
    ]

    early = _diagnose_before(src, kind)
    if early:
        shutil.rmtree(dest, ignore_errors=True)
        return False, "\n".join(log_lines + [f"falha · {early}"]), ""

    try:
        if kind == "zip":
            try:
                n, skipped = _extract_zip(src, dest)
            except Exception as zip_exc:  # noqa: BLE001
                try:
                    shutil.rmtree(dest, ignore_errors=True)
                    dest.mkdir(parents=True, exist_ok=True)
                    n, skipped = _extract_zip_ditto(src, dest)
                    log_lines.append(f"fallback ditto após: {zip_exc}")
                except Exception as ditto_exc:  # noqa: BLE001
                    raise RuntimeError(
                        f"{zip_exc}\n(também falhou ditto: {ditto_exc})"
                    ) from ditto_exc
        elif kind == "7z":
            n, skipped = _extract_7z(src, dest)
        elif kind == "tar":
            n, skipped = _extract_tar(src, dest)
        elif kind == "gz":
            n, skipped = _extract_gz(src, dest)
        else:
            shutil.rmtree(dest, ignore_errors=True)
            return (
                False,
                "\n".join(
                    log_lines
                    + [
                        f"formato não suportado: {src.suffix or src.name}",
                        f"use {SUPPORTED_LABEL}",
                    ]
                ),
                "",
            )
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(dest, ignore_errors=True)
        hint = ""
        msg = str(exc)
        if "Bad magic number" in msg or "BadZipFile" in msg:
            hint = (
                "\n\nDica: isso quase sempre é ZIP incompleto/corrompido "
                "(download não terminou) ou arquivo que só tem extensão .zip."
            )
        return False, f"falha ao descompactar: {exc}{hint}", ""

    files = _list_tree(dest)
    log_lines.append(f"ok · {n} arquivo(s) extraído(s)")
    for note in skipped[:12]:
        log_lines.append(f"⚠ {note}")
    if len(skipped) > 12:
        log_lines.append(f"⚠ … +{len(skipped) - 12} ignorado(s)")
    log_lines.append(f"pasta · {dest}")
    listing = "\n".join(files) if files else "(vazio)"
    return True, "\n".join(log_lines), listing


def unpack(
    archive_upload: str | list[str] | None = None,
    out_dir: str | None = None,
    archive_path: str | None = None,
    trash_after: bool = True,
) -> tuple[str, str]:
    """Descompacta um ou vários arquivos. Após sucesso, envia o compactado ao Lixo.

    Prefira caminhos do Finder (vários, um por linha) para arquivos grandes.
    """
    from zip_tools.finder_mac import move_to_trash

    sources = _collect_sources(archive_upload, archive_path)
    if not sources:
        return (
            "escolha um ou mais arquivos no Finder (📁 Arquivos…) "
            "ou anexe compactados.\n"
            "Para ZIPs grandes, use sempre o Finder — não o upload.",
            "",
        )

    base_out = Path(out_dir or DEFAULT_OUT).expanduser()
    try:
        base_out.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        return f"pasta de saída inválida ({base_out}): {exc}", ""

    all_logs: list[str] = []
    all_lists: list[str] = []
    ok_n = 0
    fail_n = 0

    for i, src in enumerate(sources, start=1):
        header = f"═══ [{i}/{len(sources)}] {src.name} ═══"
        ok, log, listing = _unpack_one(src, base_out)
        block = [header, log]
        if ok:
            ok_n += 1
            if trash_after:
                trashed, trash_msg = move_to_trash(src)
                block.append(
                    f"🗑 {trash_msg}" if trashed else f"⚠ lixeira: {trash_msg}"
                )
            if listing:
                all_lists.append(f"· {src.name} →\n{listing}")
        else:
            fail_n += 1
        all_logs.append("\n".join(block))

    summary = (
        f"resumo · {ok_n} ok · {fail_n} falha(s) · "
        f"{'enviados ao Lixo após sucesso' if trash_after else 'Lixo desligado'}"
    )
    return summary + "\n\n" + "\n\n".join(all_logs), "\n\n".join(all_lists)
