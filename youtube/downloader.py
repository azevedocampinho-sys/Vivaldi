"""YouTube batch download via yt-dlp."""

from __future__ import annotations

import re
import shutil
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import gradio as gr
import yt_dlp

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "downloads"
DEFAULT_OUT.mkdir(parents=True, exist_ok=True)

URL_RE = re.compile(r"https?://[^\s<>\"']+")
RESOLUTION_CHOICES = ["360", "480", "720", "1080", "melhor disponível"]
FORMAT_CHOICES = ["MP4 (vídeo)", "MP3 (áudio)"]


def parse_urls(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    found = URL_RE.findall(raw)
    seen: set[str] = set()
    urls: list[str] = []
    for u in found:
        u = u.rstrip(").,;]")
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls


def build_ydl_opts(
    *,
    out_dir: Path,
    media_format: str,
    resolution: str,
    progress_hook: Callable | None = None,
) -> dict:
    outtmpl = str(out_dir / "%(title).200B [%(id)s].%(ext)s")
    opts: dict = {
        "outtmpl": outtmpl,
        "ignoreerrors": False,
        "noplaylist": False,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    if media_format.startswith("MP3"):
        opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        if resolution == "melhor disponível":
            fmt = "bv*+ba/b"
        else:
            h = resolution
            fmt = f"bv*[height<=?{h}]+ba/b[height<=?{h}]/bv*+ba/b"
        opts.update({"format": fmt, "merge_output_format": "mp4"})
    return opts


def download_one(
    url: str,
    out_dir: Path,
    media_format: str,
    resolution: str,
    log: Callable[[str], None],
) -> tuple[str, bool, str]:
    title_holder: dict[str, str] = {"title": url}

    def hook(d: dict) -> None:
        status = d.get("status")
        info = d.get("info_dict") or {}
        if info.get("title"):
            title_holder["title"] = info["title"]
        if status == "downloading":
            pct = d.get("_percent_str") or ""
            speed = d.get("_speed_str") or ""
            log(f"↓ {title_holder['title'][:60]} — {pct.strip()} {speed.strip()}".strip())
        elif status == "finished":
            log(f"… processando: {title_holder['title'][:70]}")

    opts = build_ydl_opts(
        out_dir=out_dir,
        media_format=media_format,
        resolution=resolution,
        progress_hook=hook,
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                return url, False, "Falha ao obter informações"
            if "entries" in info:
                entries = [e for e in (info.get("entries") or []) if e]
                name = info.get("title") or url
                return name, True, f"playlist/lote: {len(entries)} item(ns)"
            name = info.get("title") or title_holder["title"]
            return name, True, "ok"
    except Exception as exc:  # noqa: BLE001
        return title_holder["title"], False, str(exc)


def run_batch(
    urls_text: str,
    media_format: str,
    resolution: str,
    out_dir_str: str,
    workers: int,
    progress: gr.Progress = gr.Progress(track_tqdm=False),
):
    from ui.theme import progress_html

    busy_btn = gr.update(value="Baixando…", interactive=False, elem_classes=["batch-cta", "is-running"])
    idle_btn = gr.update(value="Baixar tudo", interactive=True, elem_classes=["batch-cta"])

    def pack(log_text: str, result_text: str, frac: float, label: str, *, running: bool, done: bool = False, btn=None):
        return (
            log_text,
            result_text,
            progress_html(frac, label, running=running, done=done),
            btn if btn is not None else (busy_btn if running else idle_btn),
        )

    if shutil.which("ffmpeg") is None:
        yield pack(
            "erro · ffmpeg não encontrado — brew install ffmpeg",
            "",
            0,
            "erro",
            running=False,
            btn=idle_btn,
        )
        return

    urls = parse_urls(urls_text)
    if not urls:
        yield pack("erro · cole pelo menos uma URL válida do YouTube", "", 0, "erro", running=False, btn=idle_btn)
        return

    out_dir = Path(out_dir_str.strip() or DEFAULT_OUT).expanduser()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        yield pack(f"erro · pasta inválida: {exc}", "", 0, "erro", running=False, btn=idle_btn)
        return

    workers = max(1, min(int(workers or 1), 5))
    lines: list[str] = [
        f"pasta     {out_dir}",
        f"formato   {media_format} · resolução {resolution}",
        f"fila      {len(urls)} url(s) · paralelo {workers}",
        "─" * 44,
    ]
    results: list[str] = []
    ok = fail = done = 0
    total = len(urls)

    def emit(frac: float, label: str, *, running: bool = True, finished: bool = False):
        return pack(
            "\n".join(lines),
            "\n".join(results) if results else "aguardando…",
            frac,
            label,
            running=running,
            done=finished,
            btn=idle_btn if finished else busy_btn,
        )

    yield emit(0.02, "iniciando fila…", running=True)

    def log(msg: str) -> None:
        if lines and lines[-1].startswith("↓ ") and msg.startswith("↓ "):
            lines[-1] = msg
        else:
            lines.append(msg)

    progress(0, desc="Iniciando…")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(download_one, url, out_dir, media_format, resolution, log): url
            for url in urls
        }
        for fut in as_completed(futures):
            try:
                name, success, detail = fut.result()
            except Exception:  # noqa: BLE001
                name, success, detail = futures[fut], False, traceback.format_exc(limit=2)
            done += 1
            if success:
                ok += 1
                lines.append(f"ok  {name} — {detail}")
                results.append(f"ok  {name}")
            else:
                fail += 1
                lines.append(f"falha  {name} — {detail}")
                results.append(f"falha  {name}: {detail}")
            frac = done / total
            progress(frac, desc=f"{done}/{total}")
            yield emit(frac, f"{done}/{total} concluídos · {ok} ok · {fail} falha(s)", running=True)

    lines.append("─" * 44)
    lines.append(f"feito · {ok} ok · {fail} falha(s)\n{out_dir}")
    yield emit(1.0, f"concluído · {ok} ok · {fail} falha(s)", running=False, finished=True)
