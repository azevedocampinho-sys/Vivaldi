"""YouTube batch download via yt-dlp."""

from __future__ import annotations

import html
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
) -> tuple[str, bool, str, str | None]:
    title_holder: dict[str, str] = {"title": url}
    path_holder: dict[str, str | None] = {"path": None}

    def hook(d: dict) -> None:
        status = d.get("status")
        info = d.get("info_dict") or {}
        if info.get("title"):
            title_holder["title"] = info["title"]
        if status == "downloading":
            pct = d.get("_percent_str") or ""
            log(f"{title_holder['title'][:70]} · {pct.strip()}")
        elif status == "finished":
            fp = d.get("filename")
            if fp:
                path_holder["path"] = str(fp)
            log(f"Processando {title_holder['title'][:70]}")

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
                return url, False, "Falha ao obter informações", None
            if "entries" in info:
                entries = [e for e in (info.get("entries") or []) if e]
                name = info.get("title") or url
                return name, True, f"{len(entries)} item(ns)", path_holder["path"]
            name = info.get("title") or title_holder["title"]
            path = path_holder["path"]
            if not path:
                try:
                    path = ydl.prepare_filename(info)
                    if media_format.startswith("MP3"):
                        path = str(Path(path).with_suffix(".mp3"))
                except Exception:  # noqa: BLE001
                    path = None
            return name, True, "ok", path
    except Exception as exc:  # noqa: BLE001
        return title_holder["title"], False, str(exc), None


def loading_html(title: str, subtitle: str) -> str:
    return f"""
<div class="yt-loading">
  <div class="yt-spinner" aria-hidden="true"></div>
  <p class="yt-loading-title">{html.escape(title)}</p>
  <p class="yt-loading-sub">{html.escape(subtitle)}</p>
</div>
"""


def results_html(items: list[dict], out_dir: Path, ok: int, fail: int) -> str:
    rows = []
    for item in items:
        cls = "is-ok" if item["ok"] else "is-fail"
        mark = "✓" if item["ok"] else "×"
        detail = item.get("path") or item.get("detail") or ""
        rows.append(
            f"""
<li class="yt-item {cls}">
  <span class="yt-mark">{mark}</span>
  <div class="yt-item-body">
    <strong>{html.escape(item['name'])}</strong>
    <small>{html.escape(detail)}</small>
  </div>
</li>"""
        )
    summary = f"{ok} baixado(s)" + (f" · {fail} falha(s)" if fail else "")
    return f"""
<div class="yt-done">
  <p class="yt-done-kicker">Concluído</p>
  <h2 class="yt-done-title">{html.escape(summary)}</h2>
  <p class="yt-done-sub">{html.escape(str(out_dir))}</p>
  <ul class="yt-list">
    {''.join(rows) if rows else '<li class="yt-item"><div class="yt-item-body"><strong>Nada baixado</strong></div></li>'}
  </ul>
</div>
"""


def run_batch(
    urls_text: str,
    media_format: str,
    resolution: str,
    out_dir_str: str,
    workers: int,
    progress: gr.Progress = gr.Progress(track_tqdm=False),
):
    """Yields: form_vis, loading_vis, loading_html, results_vis, results_html, run_btn."""
    busy_btn = gr.update(value="Baixando…", interactive=False, elem_classes=["batch-cta", "is-running"])
    idle_btn = gr.update(value="Baixar", interactive=True, elem_classes=["batch-cta"])

    def show_loading(title: str, subtitle: str, *, btn=None):
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            loading_html(title, subtitle),
            gr.update(visible=False),
            "",
            btn if btn is not None else busy_btn,
        )

    def show_error(message: str):
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            gr.update(visible=True),
            results_html(
                [{"name": "Não foi possível baixar", "ok": False, "detail": message, "path": None}],
                Path(out_dir_str.strip() or DEFAULT_OUT),
                0,
                1,
            ),
            idle_btn,
        )

    if shutil.which("ffmpeg") is None:
        yield show_error("ffmpeg não encontrado — brew install ffmpeg")
        return

    urls = parse_urls(urls_text)
    if not urls:
        yield show_error("Cole pelo menos uma URL válida do YouTube")
        return

    out_dir = Path(out_dir_str.strip() or DEFAULT_OUT).expanduser()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        yield show_error(f"Pasta inválida: {exc}")
        return

    workers = max(1, min(int(workers or 1), 5))
    items: list[dict] = []
    ok = fail = done = 0
    total = len(urls)
    current_msg = "Preparando…"

    def log(msg: str) -> None:
        nonlocal current_msg
        current_msg = msg

    yield show_loading("Baixando", f"0/{total} · iniciando")
    progress(0, desc="Iniciando…")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(download_one, url, out_dir, media_format, resolution, log): url
            for url in urls
        }
        for fut in as_completed(futures):
            try:
                name, success, detail, path = fut.result()
            except Exception:  # noqa: BLE001
                name, success, detail, path = futures[fut], False, traceback.format_exc(limit=2), None
            done += 1
            if success:
                ok += 1
            else:
                fail += 1
            items.append(
                {
                    "name": name,
                    "ok": success,
                    "detail": detail,
                    "path": path,
                }
            )
            frac = done / total
            progress(frac, desc=f"{done}/{total}")
            yield show_loading(
                "Baixando",
                f"{done}/{total} · {current_msg or name[:48]}",
            )

    yield (
        gr.update(visible=False),
        gr.update(visible=False),
        "",
        gr.update(visible=True),
        results_html(items, out_dir, ok, fail),
        idle_btn,
    )


def show_form_again():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        "",
        gr.update(visible=False),
        "",
        gr.update(value="Baixar", interactive=True, elem_classes=["batch-cta"]),
    )
