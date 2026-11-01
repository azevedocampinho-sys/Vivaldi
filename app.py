#!/usr/bin/env python3
"""Vivaldi — hub local: YouTube, Apple Music, Stems + Four Seasons (criação musical no M4)."""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from ai import local as llm
from apple_music import ai_studio, duplicates, filters, mutations
from apple_music import demo as am_demo
from apple_music.client import AppleMusicClient, Playlist
from four_seasons import instruments as fs_instruments
from four_seasons import studio as fs
from stems import separator as stems
from ui.theme import CSS, HEAD, THEME, THEME_CHIP, progress_html
from youtube import downloader as yt
from zip_tools import unpacker as zipu
from zip_tools.finder_mac import pick_files as zip_pick_files_dialog
from zip_tools.finder_mac import pick_folder as zip_pick_folder_dialog

ROOT = Path(__file__).resolve().parent
AUTH_HTML = ROOT / "static" / "musickit_auth.html"
load_dotenv(ROOT / ".env", override=True)

# In-memory session playlist (demo or live)
_SESSION: dict[str, Playlist | None] = {"playlist": None}


def _hero(*, back_id: str | None = None) -> str:
    back = (
        f'<button type="button" class="batch-back" data-back="{back_id}" aria-label="Voltar ao hub">← Hub</button>'
        if back_id
        else '<span class="batch-back-spacer" aria-hidden="true"></span>'
    )
    return f"""
<div class="batch-shell">
  <header class="batch-hero">
    <div class="batch-top">
      {back}
      <h1 class="batch-mark">Vivaldi</h1>
      <div class="batch-chips">
        <div class="batch-chip"><i></i> No seu Mac</div>
        {THEME_CHIP}
      </div>
    </div>
  </header>
</div>
"""


HUB_HTML = f"""
<div class="batch-shell">
  <header class="batch-hero">
    <div class="batch-top">
      <h1 class="batch-mark">Vivaldi</h1>
      <div class="batch-chips">
        <div class="batch-chip"><i></i> No seu Mac</div>
        {THEME_CHIP}
      </div>
    </div>
  </header>
  <div class="hub-grid">
    <div class="hub-portal" data-hub="hub-go-yt" role="button" tabindex="0">
      <div class="hub-portal-art" aria-hidden="true"></div>
      <div class="hub-portal-content">
        <h2 class="hub-title">YouTube</h2>
        <span class="hub-arrow" aria-hidden="true">→</span>
      </div>
    </div>
    <div class="hub-portal" data-hub="hub-go-am" role="button" tabindex="0">
      <div class="hub-portal-art" aria-hidden="true"></div>
      <div class="hub-portal-content">
        <h2 class="hub-title">Apple Music</h2>
        <span class="hub-arrow" aria-hidden="true">→</span>
      </div>
    </div>
    <div class="hub-portal" data-hub="hub-go-st" role="button" tabindex="0">
      <div class="hub-portal-art" aria-hidden="true"></div>
      <div class="hub-portal-content">
        <h2 class="hub-title">Stems</h2>
        <span class="hub-arrow" aria-hidden="true">→</span>
      </div>
    </div>
    <div class="hub-portal" data-hub="hub-go-fs" role="button" tabindex="0">
      <div class="hub-portal-art" aria-hidden="true"></div>
      <div class="hub-portal-content">
        <h2 class="hub-title">Four Seasons</h2>
        <span class="hub-arrow" aria-hidden="true">→</span>
      </div>
    </div>
    <div class="hub-portal" data-hub="hub-go-zip" role="button" tabindex="0">
      <div class="hub-portal-art" aria-hidden="true"></div>
      <div class="hub-portal-content">
        <h2 class="hub-title">ZIP</h2>
        <span class="hub-arrow" aria-hidden="true">→</span>
      </div>
    </div>
  </div>
</div>
"""

FS_SEASONS_HTML = """
<div class="fs-seasons">
  <div class="fs-season-card" data-s="spring"><p class="fs-name">Primavera</p><p class="fs-phase">Pré-produção</p></div>
  <div class="fs-season-card" data-s="summer"><p class="fs-name">Verão</p><p class="fs-phase">Produção</p></div>
  <div class="fs-season-card" data-s="autumn"><p class="fs-name">Outono</p><p class="fs-phase">Arranjo</p></div>
  <div class="fs-season-card" data-s="winter"><p class="fs-name">Inverno</p><p class="fs-phase">Pós-produção</p></div>
</div>
"""


def show_hub():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def show_youtube():
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def show_apple():
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def show_stems():
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def show_four_seasons():
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
    )


def show_zip():
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def apple_connection_status(dev_token: str, user_token: str, storefront: str) -> str:
    client = AppleMusicClient(dev_token or None, user_token or None, storefront or "br")
    return f"{client.status_line()}\n{llm.status_report()}"


def ensure_ai_model(current_model: str):
    """Checa registry e atualiza tag estável se o digest mudou."""
    target = (current_model or "").strip() or None
    result = llm.ensure_stable_model(target, auto_update=True)
    return result.model, result.message


def refresh_playlists(dev_token: str, user_token: str, storefront: str):
    client = AppleMusicClient(dev_token or None, user_token or None, storefront or "br")
    if not client.configured:
        choices = am_demo.demo_playlist_choices()
        return gr.update(choices=choices, value=choices[0][1]), "demo · playlist de exemplo carregável"
    try:
        choices = client.list_library_playlists()
        if not choices:
            return gr.update(choices=[], value=None), "nenhuma playlist na biblioteca"
        return gr.update(choices=choices, value=choices[0][1]), f"{len(choices)} playlist(s) · cache gentil"
    except Exception as exc:  # noqa: BLE001
        choices = am_demo.demo_playlist_choices()
        return (
            gr.update(choices=choices, value=choices[0][1]),
            f"falha API ({exc}) — caindo no demo",
        )


def load_playlist(playlist_id: str, dev_token: str, user_token: str, storefront: str):
    client = AppleMusicClient(dev_token or None, user_token or None, storefront or "br")
    try:
        if not client.configured or (playlist_id or "").startswith("demo."):
            pl = am_demo.load_demo_playlist()
        else:
            pl = client.get_library_playlist_tracks(playlist_id)
        _SESSION["playlist"] = pl
        dups = duplicates.find_duplicates(pl)
        report = duplicates.format_duplicate_report(pl, dups)
        genres = ["Todos"] + filters.available_genres(pl)
        years = ["Todos"] + filters.available_years(pl)
        table = filters.format_track_table(pl.tracks)
        alert = ""
        if dups:
            alert = f"⚠ {len(dups)} grupo(s) com músicas duplicadas nesta playlist"
        else:
            alert = "✓ sem duplicatas"
        return (
            report,
            alert,
            table,
            gr.update(choices=genres, value="Todos"),
            gr.update(choices=years, value="Todos"),
            f"carregada · {pl.name} · {len(pl.tracks)} faixas",
        )
    except Exception as exc:  # noqa: BLE001
        return str(exc), "erro", "", gr.update(), gr.update(), f"erro · {exc}"


def apply_track_filters(year: str, genre: str):
    pl = _SESSION.get("playlist")
    if not pl:
        return "carregue uma playlist primeiro"
    tracks = filters.apply_filters(pl, year=year, genre=genre)
    return filters.format_track_table(tracks)


def run_recommend(model: str):
    pl = _SESSION.get("playlist")
    if not pl:
        return "carregue uma playlist primeiro"
    return ai_studio.recommend(pl, model or llm.DEFAULT_MODEL)


def run_sequence(model: str):
    pl = _SESSION.get("playlist")
    if not pl:
        return "carregue uma playlist primeiro"
    return ai_studio.best_sequence(pl, model or llm.DEFAULT_MODEL)


def apply_dedupe_to_apple(dev_token: str, user_token: str, storefront: str):
    pl = _SESSION.get("playlist")
    if not pl:
        return "carregue uma playlist primeiro", "sem playlist"
    client = AppleMusicClient(dev_token or None, user_token or None, storefront or "br")
    msg = mutations.apply_remove_duplicates(client, pl)
    return msg, msg.split("\n", 1)[0]


def apply_sequence_to_apple(model: str, dev_token: str, user_token: str, storefront: str):
    pl = _SESSION.get("playlist")
    if not pl:
        return "carregue uma playlist primeiro"
    client = AppleMusicClient(dev_token or None, user_token or None, storefront or "br")
    ordered, note = ai_studio.ordered_tracks(pl, model or llm.DEFAULT_MODEL)
    if not ordered:
        return note
    result = mutations.apply_track_order(client, pl, ordered)
    return f"{result}\n\nIA: {note}"


def apply_filter_to_apple(year: str, genre: str, dev_token: str, user_token: str, storefront: str):
    pl = _SESSION.get("playlist")
    if not pl:
        return "carregue uma playlist primeiro"
    tracks = filters.apply_filters(pl, year=year, genre=genre)
    label_bits = []
    if year and year != "Todos":
        label_bits.append(str(year))
    if genre and genre != "Todos":
        label_bits.append(str(genre))
    label = " · ".join(label_bits) if label_bits else "filtro"
    client = AppleMusicClient(dev_token or None, user_token or None, storefront or "br")
    return mutations.apply_filtered_playlist(client, pl, tracks, label=label)


def run_chat(message: str, history: list, model: str):
    pl = _SESSION.get("playlist")
    if not (message or "").strip():
        return history, history
    # history as list of dicts for Gradio Chatbot messages format, or tuples
    pairs: list[tuple[str, str]] = []
    if history:
        # Gradio 6 may use list[{"role","content"}] or tuples
        if isinstance(history[0], dict):
            user_buf = None
            for item in history:
                if item.get("role") == "user":
                    user_buf = item.get("content", "")
                elif item.get("role") == "assistant" and user_buf is not None:
                    pairs.append((user_buf, item.get("content", "")))
                    user_buf = None
        else:
            pairs = [(a, b) for a, b in history]

    answer, pairs = ai_studio.chat_about(pl, message, pairs, model or llm.DEFAULT_MODEL)
    # Return messages format for Gradio 6
    messages = []
    for q, a in pairs:
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a})
    return messages, messages


with gr.Blocks(title="Vivaldi") as demo:
    # —— HUB ——
    with gr.Column(visible=True, elem_classes=["batch-shell"]) as hub_view:
        gr.HTML(HUB_HTML)
        with gr.Row(elem_classes=["hub-nav-row"]):
            btn_yt = gr.Button("YouTube", elem_id="hub-go-yt", elem_classes=["hub-nav-btn"])
            btn_am = gr.Button("Apple Music", elem_id="hub-go-am", elem_classes=["hub-nav-btn"])
            btn_st = gr.Button("Stems", elem_id="hub-go-st", elem_classes=["hub-nav-btn"])
            btn_fs = gr.Button("Four Seasons", elem_id="hub-go-fs", elem_classes=["hub-nav-btn"])
            btn_zip = gr.Button("ZIP", elem_id="hub-go-zip", elem_classes=["hub-nav-btn"])

    # —— YOUTUBE ——
    with gr.Column(visible=False, elem_classes=["yt-studio"]) as yt_view:
        with gr.Row(elem_classes=["back-row"]):
            back_yt = gr.Button("← Hub", elem_id="back-yt", elem_classes=["hub-nav-btn"])
        gr.HTML(_hero(back_id="back-yt"))

        with gr.Column(visible=True, elem_classes=["yt-form"]) as yt_form:
            with gr.Group(elem_classes=["batch-panel"]):
                urls = gr.Textbox(
                    label="Links",
                    lines=8,
                    placeholder="Cole um link por linha. Playlists também funcionam.",
                )
            with gr.Group(elem_classes=["yt-controls"]):
                with gr.Row():
                    media_format = gr.Radio(
                        yt.FORMAT_CHOICES, value="MP4 (vídeo)", label="Formato", scale=2
                    )
                    resolution = gr.Dropdown(
                        yt.RESOLUTION_CHOICES, value="1080", label="Resolução máx.", scale=1
                    )
                    workers = gr.Slider(1, 5, value=2, step=1, label="Paralelo", scale=2)
                out_dir = gr.Textbox(label="Pasta de saída", value=str(yt.DEFAULT_OUT))
            run_btn = gr.Button("Baixar", variant="primary", elem_classes=["batch-cta"])

        with gr.Column(visible=False, elem_classes=["yt-stage"]) as yt_loading:
            yt_loading_html = gr.HTML(yt.loading_html("Baixando", "Preparando…"))

        with gr.Column(visible=False, elem_classes=["yt-stage"]) as yt_results:
            yt_results_html = gr.HTML("")
            yt_again = gr.Button("Nova descarga", elem_classes=["batch-cta"])

        yt_flow_outs = [yt_form, yt_loading, yt_loading_html, yt_results, yt_results_html, run_btn]
        run_btn.click(
            fn=yt.run_batch,
            inputs=[urls, media_format, resolution, out_dir, workers],
            outputs=yt_flow_outs,
        )
        yt_again.click(fn=yt.show_form_again, outputs=yt_flow_outs)

    # —— APPLE MUSIC ——
    AM_SECTIONS = [
        "Playlist e duplicatas",
        "Filtros",
        "IA local",
        "Chat musical",
        "Conexão",
    ]
    AM_BLURBS = {
        "Playlist e duplicatas": "Detecte repetidas e grave a versão limpa no Apple Music com um clique.",
        "Filtros": "Refine por ano/gênero e publique o recorte como playlist nova.",
        "IA local": "Sequência ideal no Mac — e aplica criando a playlist ordenada na Apple.",
        "Chat musical": "Pergunte sobre artistas, álbuns, eras e curiosidades.",
        "Conexão": "Tokens oficiais da Apple e status do Ollama.",
    }

    AM_NEEDS_PLAYLIST = {"Playlist e duplicatas", "Filtros", "IA local"}

    def am_switch_section(section: str):
        section = section or AM_SECTIONS[0]
        blurb = AM_BLURBS.get(section, "")
        flags = [section == s for s in AM_SECTIONS]
        return (
            f'<p class="am-command-sub">{blurb}</p>',
            gr.update(visible=section in AM_NEEDS_PLAYLIST),
            *(gr.update(visible=f) for f in flags),
        )

    with gr.Column(visible=False, elem_classes=["am-studio"]) as am_view:
        with gr.Row(elem_classes=["back-row"]):
            back_am = gr.Button("← Hub", elem_id="back-am", elem_classes=["hub-nav-btn"])
        gr.HTML(_hero(back_id="back-am"))

        with gr.Group(elem_classes=["am-command"]):
            gr.HTML('<p class="am-command-title">Área</p>')
            am_section_blurb = gr.HTML(
                f'<p class="am-command-sub">{AM_BLURBS[AM_SECTIONS[0]]}</p>'
            )
            am_section = gr.Radio(
                choices=AM_SECTIONS,
                value=AM_SECTIONS[0],
                label="Área",
                show_label=False,
                elem_classes=["am-area-radio"],
                interactive=True,
            )

        with gr.Column(visible=True, elem_classes=["am-playlist-wrap"]) as am_playlist_wrap:
            with gr.Group(elem_classes=["am-playlist-strip"]):
                with gr.Row():
                    am_playlist = gr.Dropdown(
                        label="Playlist ativa", choices=[], value=None, scale=3
                    )
                    am_refresh = gr.Button("Atualizar lista", scale=1)
                    am_load = gr.Button("Abrir", variant="primary", scale=1)

        # —— painéis (só a área selecionada fica visível) ——
        with gr.Column(visible=True, elem_classes=["am-section-panel"]) as am_panel_playlist:
            am_alert = gr.Textbox(label="Alerta de duplicatas", interactive=False)
            am_dup_report = gr.Textbox(
                label="Relatório", lines=12, interactive=False, elem_classes=["batch-output"]
            )
            am_dedupe_btn = gr.Button(
                "Remover duplicatas no Apple Music",
                variant="primary",
                elem_classes=["batch-cta"],
            )
            am_write_status = gr.Textbox(
                label="Escrita no Apple Music",
                interactive=False,
                lines=5,
                elem_classes=["batch-output"],
            )
            gr.HTML(
                '<p class="batch-foot" style="margin-top:8px">'
                "A API oficial da Apple não apaga faixas da playlist original. "
                "Com um clique o Vivaldi tenta remover in-place; se a Apple bloquear, "
                "cria automaticamente uma playlist nova já limpa na sua biblioteca."
                "</p>"
            )

        with gr.Column(visible=False, elem_classes=["am-section-panel"]) as am_panel_filters:
            with gr.Row():
                am_year = gr.Dropdown(label="Filtro ano", choices=["Todos"], value="Todos")
                am_genre = gr.Dropdown(label="Filtro gênero", choices=["Todos"], value="Todos")
                am_filter = gr.Button("Aplicar filtros", variant="primary")
            am_table = gr.Textbox(
                label="Faixas filtradas", lines=14, interactive=False, elem_classes=["batch-output"]
            )
            am_filter_write = gr.Button(
                "Criar playlist filtrada no Apple Music",
                variant="primary",
                elem_classes=["batch-cta"],
            )
            am_filter_status = gr.Textbox(
                label="Escrita no Apple Music",
                interactive=False,
                lines=4,
                elem_classes=["batch-output"],
            )

        with gr.Column(visible=False, elem_classes=["am-section-panel"]) as am_panel_ai:
            with gr.Row():
                am_model = gr.Textbox(label="Modelo Ollama", value=llm.DEFAULT_MODEL)
                am_update = gr.Button("Atualizar IA")
            am_ai_status = gr.Textbox(
                label="Status do modelo",
                value=llm.status_report(),
                interactive=False,
                lines=2,
            )
            with gr.Row():
                am_rec = gr.Button("Indicar músicas", variant="primary")
                am_seq = gr.Button("Melhor sequência", variant="primary")
            am_seq_write = gr.Button(
                "Aplicar sequência no Apple Music",
                variant="primary",
                elem_classes=["batch-cta"],
            )
            am_ai_out = gr.Textbox(
                label="Resultado da IA", lines=14, interactive=False, elem_classes=["batch-output"]
            )

        with gr.Column(visible=False, elem_classes=["am-section-panel"]) as am_panel_chat:
            am_chat = gr.Chatbot(label="Chat musical", height=380)
            am_msg = gr.Textbox(
                label="Pergunta",
                placeholder="Ex.: curiosidades sobre The Weeknd nos anos 2010…",
            )
            am_ask = gr.Button("Enviar", variant="primary", elem_classes=["batch-cta"])
            am_hist = gr.State([])

        with gr.Column(visible=False, elem_classes=["am-section-panel"]) as am_panel_conn:
            gr.Markdown(
                "Tokens preferencialmente no `.env`. Campos vazios usam o `.env` automaticamente.  \n"
                "Safari (user token): "
                "[http://127.0.0.1:7860/am-auth/musickit_auth.html]"
                "(http://127.0.0.1:7860/am-auth/musickit_auth.html)  \n"
                "**Sem tokens = modo demo** (playlist de exemplo, sem gravar na Apple)."
            )
            am_dev = gr.Textbox(
                label="Developer token",
                type="password",
                value=os.getenv("APPLE_MUSIC_DEVELOPER_TOKEN", ""),
            )
            am_user = gr.Textbox(
                label="Music User Token",
                type="password",
                value=os.getenv("APPLE_MUSIC_USER_TOKEN", ""),
            )
            am_sf = gr.Textbox(
                label="Storefront",
                value=os.getenv("APPLE_MUSIC_STOREFRONT", "br") or "br",
            )
            am_status = gr.Textbox(
                label="Status",
                interactive=False,
                lines=3,
                value=apple_connection_status("", "", os.getenv("APPLE_MUSIC_STOREFRONT", "br") or "br"),
            )
            am_check = gr.Button("Checar conexão", variant="primary")

        am_section.change(
            am_switch_section,
            am_section,
            [
                am_section_blurb,
                am_playlist_wrap,
                am_panel_playlist,
                am_panel_filters,
                am_panel_ai,
                am_panel_chat,
                am_panel_conn,
            ],
        )
        am_check.click(apple_connection_status, [am_dev, am_user, am_sf], am_status)
        am_refresh.click(refresh_playlists, [am_dev, am_user, am_sf], [am_playlist, am_status])
        am_load.click(
            load_playlist,
            [am_playlist, am_dev, am_user, am_sf],
            [am_dup_report, am_alert, am_table, am_genre, am_year, am_status],
        )
        am_filter.click(apply_track_filters, [am_year, am_genre], am_table)
        am_dedupe_btn.click(
            apply_dedupe_to_apple,
            [am_dev, am_user, am_sf],
            [am_write_status, am_status],
        )
        am_filter_write.click(
            apply_filter_to_apple,
            [am_year, am_genre, am_dev, am_user, am_sf],
            am_filter_status,
        )
        am_update.click(ensure_ai_model, am_model, [am_model, am_ai_status])
        am_rec.click(run_recommend, am_model, am_ai_out)
        am_seq.click(run_sequence, am_model, am_ai_out)
        am_seq_write.click(
            apply_sequence_to_apple,
            [am_model, am_dev, am_user, am_sf],
            am_ai_out,
        )
        am_ask.click(run_chat, [am_msg, am_hist, am_model], [am_chat, am_hist]).then(
            lambda: "", None, am_msg
        )

        gr.HTML(
            '<p class="batch-foot">Escrita oficial: cria playlists / adiciona faixas em api.music.apple.com. '
            "Remover/reordenar in-place costuma ser bloqueado pela Apple — o Vivaldi grava uma playlist nova. "
            "Anti-ban: cache · backoff 429 · sem download.</p>"
        )

    # —— STEMS (HTDemucs) ——
    with gr.Column(visible=False) as stems_view:
        with gr.Row(elem_classes=["back-row"]):
            back_st = gr.Button("← Hub", elem_id="back-st", elem_classes=["hub-nav-btn"])
        gr.HTML(_hero(back_id="back-st"))
        gr.Markdown(f"**Status:** {stems.status_line()}")
        stem_file = gr.Audio(
            label="Áudio de entrada",
            type="filepath",
            sources=["upload"],
        )
        with gr.Row():
            stem_model = gr.Dropdown(stems.MODELS, value="htdemucs", label="Modelo")
            stem_mode = gr.Dropdown(stems.MODES, value=stems.MODES[0], label="Modo")
            stem_shifts = gr.Slider(0, 2, value=1, step=1, label="Shifts (qualidade↑ / tempo↑)")
        stem_out = gr.Textbox(label="Pasta de saída", value=str(stems.DEFAULT_OUT))
        stem_btn = gr.Button("Separar", variant="primary", elem_classes=["batch-cta"])
        stem_progress = gr.HTML(
            progress_html(0, "Pronto", running=False),
        )
        with gr.Row():
            stem_log = gr.Textbox(label="Log", lines=14, interactive=False, elem_classes=["batch-output"])
            stem_files = gr.Textbox(label="Arquivos gerados", lines=14, interactive=False, elem_classes=["batch-output"])
        stem_btn.click(
            fn=stems.separate,
            inputs=[stem_file, stem_model, stem_mode, stem_out, stem_shifts],
            outputs=[stem_log, stem_files, stem_progress, stem_btn],
        )
        gr.HTML(
            '<p class="batch-foot">Roda 100% offline. Use áudios que você tem direito de editar. '
            "Instrumental rápido = vocals + no_vocals (renomeado para *__instrumental).</p>"
        )

    # —— FOUR SEASONS ——
    FS_SECTIONS = ["Primavera", "Verão", "Outono", "Inverno"]
    FS_BLURBS = {
        "Primavera": "Pré-produção: conceito, mood e DNA das suas playlists Apple Music.",
        "Verão": "Produção: cantarolar, rack de instrumentos (+) e gerar camadas.",
        "Outono": "Arranjo: chat para ajustar camadas — inspire-se em faixa ou artista.",
        "Inverno": "Pós: mix, CIFRA e partitura ABC por instrumento + export.",
    }
    FS_SEASON_IDS = {
        "Primavera": "spring",
        "Verão": "summer",
        "Outono": "autumn",
        "Inverno": "winter",
    }

    def fs_switch(section: str):
        section = section or FS_SECTIONS[0]
        fs.set_season(FS_SEASON_IDS.get(section, "spring"))
        flags = [section == s for s in FS_SECTIONS]
        return (
            f'<p class="am-command-sub">{FS_BLURBS[section]}</p>',
            *(gr.update(visible=f) for f in flags),
            fs.project_status(),
        )

    def fs_save_spring(title, concept, mood, key, mode, tempo):
        return fs.update_preproduction(
            title, concept, mood, key, mode, tempo, _SESSION.get("playlist")
        ), fs.project_status()

    def fs_run_spring(model):
        return fs.run_spring(model or llm.DEFAULT_MODEL, _SESSION.get("playlist")), fs.project_status()

    def fs_sync_refs():
        return fs.sync_apple_references(_SESSION.get("playlist")), fs.project_status()

    def fs_add_inst(inst_id):
        msg, rack = fs.add_instrument(inst_id)
        return msg, rack, fs.project_status()

    def fs_remove_inst(inst_id):
        msg, rack = fs.remove_instrument(inst_id)
        return msg, rack, fs.project_status()

    def fs_hum(path):
        return fs.ingest_humming(path), fs.project_status()

    def fs_run_summer(model):
        text, rack = fs.run_summer(model or llm.DEFAULT_MODEL, _SESSION.get("playlist"))
        return text, rack, fs.project_status()

    def fs_chat(message, history, model):
        messages, pairs, rack = fs.run_autumn_chat(
            message, history, model or llm.DEFAULT_MODEL, _SESSION.get("playlist")
        )
        return messages, pairs, rack, fs.project_status()

    def fs_run_winter(model):
        mix, scores, status = fs.run_winter(model or llm.DEFAULT_MODEL, _SESSION.get("playlist"))
        return mix, scores, status, fs.project_status()

    with gr.Column(visible=False) as fs_view:
        with gr.Row(elem_classes=["back-row"]):
            back_fs = gr.Button("← Hub", elem_id="back-fs", elem_classes=["hub-nav-btn"])
        gr.HTML(_hero(back_id="back-fs"))
        fs_status = gr.Textbox(
            label="Projeto",
            value=fs.project_status(),
            interactive=False,
            lines=3,
        )

        with gr.Group(elem_classes=["am-command"]):
            gr.HTML('<p class="am-command-title">Estação</p>')
            fs_blurb = gr.HTML(f'<p class="am-command-sub">{FS_BLURBS[FS_SECTIONS[0]]}</p>')
            fs_section = gr.Radio(
                choices=FS_SECTIONS,
                value=FS_SECTIONS[0],
                label="Estação",
                show_label=False,
                elem_classes=["am-area-radio"],
                interactive=True,
            )

        # Primavera
        with gr.Column(visible=True, elem_classes=["am-section-panel"]) as fs_panel_spring:
            with gr.Row():
                fs_title = gr.Textbox(label="Título", value="Sem título", scale=2)
                fs_key = gr.Textbox(label="Tom", value="C", scale=1)
                fs_mode = gr.Dropdown(label="Modo", choices=["maior", "menor"], value="maior", scale=1)
                fs_tempo = gr.Slider(60, 180, value=100, step=1, label="BPM", scale=2)
            fs_mood = gr.Textbox(label="Mood", placeholder="ex.: noturno, íntimo, cinematográfico…")
            fs_concept = gr.Textbox(
                label="Conceito / brief",
                lines=4,
                placeholder="Sobre o que é a música? Que história ela conta?",
            )
            fs_refs = gr.Textbox(
                label="DNA Apple Music",
                lines=5,
                interactive=False,
                value="Abra uma playlist no Apple Music e toque Sincronizar referências.",
                elem_classes=["batch-output"],
            )
            with gr.Row():
                fs_sync = gr.Button("Sincronizar referências")
                fs_save_pre = gr.Button("Salvar pré-produção", variant="primary")
                fs_brief = gr.Button("Gerar brief (IA M4)", variant="primary")
            fs_spring_out = gr.Textbox(
                label="Brief de pré-produção",
                lines=14,
                interactive=False,
                elem_classes=["batch-output"],
            )

        # Verão
        with gr.Column(visible=False, elem_classes=["am-section-panel"]) as fs_panel_summer:
            fs_hum_audio = gr.Audio(
                label="Cantarolar / melodia guia",
                type="filepath",
                sources=["microphone", "upload"],
            )
            fs_hum_btn = gr.Button("Analisar cantarolar")
            fs_hum_out = gr.Textbox(label="Análise do take", lines=4, interactive=False)
            with gr.Group(elem_classes=["fs-rack"]):
                with gr.Row():
                    fs_inst = gr.Dropdown(
                        label="Instrumento",
                        choices=fs_instruments.CHOICES,
                        value=fs_instruments.CHOICES[0][1],
                        scale=3,
                    )
                    fs_add = gr.Button("+ Adicionar", variant="primary", scale=1)
                    fs_del = gr.Button("Remover", scale=1)
                fs_rack = gr.Textbox(
                    label="Rack de camadas",
                    lines=12,
                    interactive=False,
                    value=fs.layers_view(),
                    elem_classes=["batch-output"],
                )
                fs_inst_msg = gr.Textbox(label="Rack", interactive=False, lines=1)
            fs_produce = gr.Button("Produzir camadas (IA M4)", variant="primary", elem_classes=["batch-cta"])
            fs_summer_out = gr.Textbox(
                label="Produção",
                lines=14,
                interactive=False,
                elem_classes=["batch-output"],
            )

        # Outono
        with gr.Column(visible=False, elem_classes=["am-section-panel"]) as fs_panel_autumn:
            fs_rack_aut = gr.Textbox(
                label="Camadas atuais",
                lines=10,
                interactive=False,
                value=fs.layers_view(),
                elem_classes=["batch-output"],
            )
            fs_chatbot = gr.Chatbot(label="Chat de arranjo", height=360)
            fs_msg = gr.Textbox(
                label="Ajuste",
                placeholder="Ex.: inspire-se no clima de Blinding Lights; deixe o baixo mais round…",
            )
            fs_ask = gr.Button("Enviar ao arranjo", variant="primary", elem_classes=["batch-cta"])
            fs_hist = gr.State([])

        # Inverno
        with gr.Column(visible=False, elem_classes=["am-section-panel"]) as fs_panel_winter:
            fs_finish = gr.Button(
                "Fechar Inverno · mix + cifras + partituras",
                variant="primary",
                elem_classes=["batch-cta"],
            )
            fs_mix = gr.Textbox(
                label="Pós-produção / mix",
                lines=12,
                interactive=False,
                elem_classes=["batch-output"],
            )
            fs_scores = gr.Textbox(
                label="CIFRA + partitura (ABC) por instrumento",
                lines=16,
                interactive=False,
                elem_classes=["batch-output"],
            )
            fs_export = gr.Textbox(label="Export", interactive=False, lines=3)

        fs_model = gr.Textbox(label="Modelo Ollama", value=llm.DEFAULT_MODEL)

        fs_section.change(
            fs_switch,
            fs_section,
            [fs_blurb, fs_panel_spring, fs_panel_summer, fs_panel_autumn, fs_panel_winter, fs_status],
        )
        fs_sync.click(fs_sync_refs, outputs=[fs_refs, fs_status])
        fs_save_pre.click(
            fs_save_spring,
            [fs_title, fs_concept, fs_mood, fs_key, fs_mode, fs_tempo],
            [fs_spring_out, fs_status],
        )
        fs_brief.click(fs_run_spring, fs_model, [fs_spring_out, fs_status])
        fs_hum_btn.click(fs_hum, fs_hum_audio, [fs_hum_out, fs_status])
        fs_add.click(fs_add_inst, fs_inst, [fs_inst_msg, fs_rack, fs_status]).then(
            lambda: fs.layers_view(), None, fs_rack_aut
        )
        fs_del.click(fs_remove_inst, fs_inst, [fs_inst_msg, fs_rack, fs_status]).then(
            lambda: fs.layers_view(), None, fs_rack_aut
        )
        fs_produce.click(fs_run_summer, fs_model, [fs_summer_out, fs_rack, fs_status]).then(
            lambda: fs.layers_view(), None, fs_rack_aut
        )
        fs_ask.click(
            fs_chat, [fs_msg, fs_hist, fs_model], [fs_chatbot, fs_hist, fs_rack_aut, fs_status]
        ).then(lambda: "", None, fs_msg).then(lambda: fs.layers_view(), None, fs_rack)
        fs_finish.click(fs_run_winter, fs_model, [fs_mix, fs_scores, fs_export, fs_status])

        gr.HTML(
            '<p class="batch-foot">Four Seasons usa a playlist aberta no Apple Music como referência '
            "estética e a IA local (Ollama) no M4. CIFRA + ABC em four_seasons_out/.</p>"
        )

    # —— ZIP ——
    with gr.Column(visible=False, elem_classes=["zip-studio"]) as zip_view:
        with gr.Row(elem_classes=["back-row"]):
            back_zip = gr.Button("← Hub", elem_id="back-zip", elem_classes=["hub-nav-btn"])
        gr.HTML(_hero(back_id="back-zip"))
        with gr.Group(elem_classes=["batch-panel"]):
            with gr.Row():
                zip_path = gr.Textbox(
                    label="Arquivos no Mac (um caminho por linha)",
                    placeholder="Clique em 📁 Arquivos… (múltipla seleção) ou cole caminhos",
                    lines=4,
                    scale=4,
                )
                zip_pick_file = gr.Button("📁 Arquivos…", scale=1)
            zip_file = gr.File(
                label="Upload browser (vários; só arquivos pequenos)",
                file_count="multiple",
                type="filepath",
                file_types=[".zip", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"],
            )
            with gr.Row():
                zip_out = gr.Textbox(
                    label="Pasta de saída",
                    value=str(zipu.DEFAULT_OUT),
                    scale=4,
                )
                zip_pick_dir = gr.Button("📁 Pasta…", scale=1)
            zip_trash = gr.Checkbox(
                label="Após sucesso, enviar o .zip (ou tar/gz) para a Lixeira",
                value=True,
            )
            zip_btn = gr.Button("Descompactar", variant="primary", elem_classes=["batch-cta"])
        with gr.Row():
            zip_log = gr.Textbox(
                label="Resultado",
                lines=12,
                interactive=False,
                elem_classes=["batch-output"],
            )
            zip_files = gr.Textbox(
                label="Arquivos extraídos",
                lines=12,
                interactive=False,
                elem_classes=["batch-output"],
            )
        zip_pick_file.click(fn=zip_pick_files_dialog, outputs=zip_path)
        zip_pick_dir.click(fn=zip_pick_folder_dialog, outputs=zip_out)
        zip_btn.click(
            fn=zipu.unpack,
            inputs=[zip_file, zip_out, zip_path, zip_trash],
            outputs=[zip_log, zip_files],
        )
        gr.HTML(
            f'<p class="batch-foot">Formatos: {zipu.SUPPORTED_LABEL}. '
            "Vários de uma vez via 📁 Arquivos…. "
            "Arquivos grandes: use o Finder (não o upload). "
            "Sucesso → Lixeira (recuperável). Proteção zip-slip ativa.</p>"
        )

    # navigation + auto-update IA ao entrar nos estúdios com IA
    nav_outs = [hub_view, yt_view, am_view, stems_view, fs_view, zip_view]
    btn_yt.click(show_youtube, outputs=nav_outs)
    btn_am.click(show_apple, outputs=nav_outs).then(
        ensure_ai_model, am_model, [am_model, am_ai_status]
    ).then(
        apple_connection_status, [am_dev, am_user, am_sf], am_status
    ).then(
        refresh_playlists, [am_dev, am_user, am_sf], [am_playlist, am_status]
    )
    btn_st.click(show_stems, outputs=nav_outs)
    btn_fs.click(show_four_seasons, outputs=nav_outs).then(
        fs_sync_refs, outputs=[fs_refs, fs_status]
    )
    btn_zip.click(show_zip, outputs=nav_outs)
    back_yt.click(show_hub, outputs=nav_outs)
    back_am.click(show_hub, outputs=nav_outs)
    back_st.click(show_hub, outputs=nav_outs)
    back_fs.click(show_hub, outputs=nav_outs)
    back_zip.click(show_hub, outputs=nav_outs)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    # MusicKit JS não roda em file:// — auth page em localhost ao lado do Gradio
    api = FastAPI()

    @api.get("/am-auth/musickit_auth.html")
    async def _musickit_auth_page():
        return FileResponse(AUTH_HTML, media_type="text/html; charset=utf-8")

    api.mount("/am-auth", StaticFiles(directory=str(ROOT / "static")), name="am-auth")

    demo.queue()
    app = gr.mount_gradio_app(
        api,
        demo,
        path="/",
        theme=THEME,
        css=CSS,
        head=HEAD,
    )
    uvicorn.run(app, host="127.0.0.1", port=7860, log_level="info")
