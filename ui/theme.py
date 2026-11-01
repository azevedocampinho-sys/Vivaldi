"""Vivaldi — visual system Apple-premium (SF Pro + Interactive Blue + Instrument Serif brand)."""

from __future__ import annotations

import base64
from pathlib import Path

import gradio as gr

_HUB_ART_DIR = Path(__file__).resolve().parents[1] / "static" / "hub"
_HUB_ART_FILES = {
    "hub-go-yt": "youtube.jpg",
    "hub-go-am": "apple-music.jpg",
    "hub-go-st": "stems.jpg",
    "hub-go-fs": "four-seasons.jpg",
    "hub-go-zip": "zip.jpg",
}


def _hub_art_css() -> str:
    rules: list[str] = []
    for hub_id, filename in _HUB_ART_FILES.items():
        path = _HUB_ART_DIR / filename
        if not path.exists():
            continue
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            f'.hub-portal[data-hub="{hub_id}"] .hub-portal-art{{'
            f'background-image:url("data:image/jpeg;base64,{payload}");}}'
        )
    return "\n".join(rules)

HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<script>
(function () {
  function applyTheme(dark) {
    var root = document.documentElement;
    root.classList.toggle("vivaldi-dark", dark);
    root.classList.toggle("vivaldi-light", !dark);
    root.style.colorScheme = dark ? "dark" : "light";
    document.body && document.body.classList.toggle("dark", dark);
    document.querySelectorAll(".gradio-container, .main, .app").forEach(function (n) {
      n.classList.toggle("dark", dark);
    });
    document.querySelectorAll("[data-theme-label]").forEach(function (n) {
      n.textContent = dark ? "Escuro" : "Claro";
    });
  }
  try {
    applyTheme(localStorage.getItem("vivaldi-theme") === "dark");
  } catch (e) {
    applyTheme(false);
  }
  window.toggleBatchTheme = function () {
    var dark = !document.documentElement.classList.contains("vivaldi-dark");
    try { localStorage.setItem("vivaldi-theme", dark ? "dark" : "light"); } catch (e) {}
    applyTheme(dark);
  };
  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(document.documentElement.classList.contains("vivaldi-dark"));
  });
  function clickById(id) {
    var root = document.getElementById(id);
    if (!root) return;
    var btn = root.tagName === "BUTTON" ? root : root.querySelector("button");
    if (btn) btn.click();
  }
  document.addEventListener("click", function (e) {
    var portal = e.target.closest("[data-hub]");
    if (portal) {
      e.preventDefault();
      clickById(portal.getAttribute("data-hub"));
      return;
    }
    var back = e.target.closest("[data-back]");
    if (back) {
      e.preventDefault();
      clickById(back.getAttribute("data-back"));
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var el = e.target.closest("[data-hub], [data-back]");
    if (!el) return;
    e.preventDefault();
    clickById(el.getAttribute("data-hub") || el.getAttribute("data-back"));
  });
})();
</script>
"""

THEME = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#eff6ff",
        c100="#dbeafe",
        c200="#bfdbfe",
        c300="#93c5fd",
        c400="#60a5fa",
        c500="#0071e3",
        c600="#0066cc",
        c700="#0055b3",
        c800="#004499",
        c900="#003366",
        c950="#001a33",
    ),
    secondary_hue="zinc",
    neutral_hue=gr.themes.Color(
        c50="#f5f5f7",
        c100="#e8e8ed",
        c200="#d2d2d7",
        c300="#b0b0b5",
        c400="#86868b",
        c500="#6e6e73",
        c600="#515154",
        c700="#424245",
        c800="#333336",
        c900="#1d1d1f",
        c950="#000000",
    ),
    font=[
        "-apple-system",
        "BlinkMacSystemFont",
        "SF Pro Text",
        "Helvetica Neue",
        "Helvetica",
        "Arial",
        "sans-serif",
    ],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace", "monospace"],
    radius_size=gr.themes.sizes.radius_xxl,
).set(
    body_background_fill="#f5f5f7",
    body_background_fill_dark="#000000",
    body_text_color="#1d1d1f",
    body_text_color_dark="#f5f5f7",
    body_text_color_subdued="#6e6e73",
    body_text_color_subdued_dark="#86868b",
    background_fill_primary="#ffffff",
    background_fill_primary_dark="#000000",
    background_fill_secondary="#f5f5f7",
    background_fill_secondary_dark="#000000",
    border_color_primary="rgba(0,0,0,0.08)",
    border_color_primary_dark="rgba(255,255,255,0.14)",
    block_background_fill="#ffffff",
    block_background_fill_dark="#000000",
    block_border_width="0px",
    block_border_color="transparent",
    block_border_color_dark="transparent",
    block_label_text_color="#6e6e73",
    block_label_text_color_dark="#86868b",
    block_label_background_fill="transparent",
    block_label_background_fill_dark="transparent",
    block_title_text_color="#1d1d1f",
    block_title_text_color_dark="#f5f5f7",
    block_radius="18px",
    input_background_fill="#f5f5f7",
    input_background_fill_dark="#000000",
    input_border_color="transparent",
    input_border_color_dark="rgba(255,255,255,0.12)",
    input_border_color_focus="#0071e3",
    input_border_color_focus_dark="#2997ff",
    input_placeholder_color="#86868b",
    input_placeholder_color_dark="#6e6e73",
    button_primary_background_fill="#0071e3",
    button_primary_background_fill_dark="#0071e3",
    button_primary_background_fill_hover="#0077ed",
    button_primary_background_fill_hover_dark="#147ce5",
    button_primary_text_color="#ffffff",
    button_primary_text_color_dark="#ffffff",
    button_primary_border_color="#0071e3",
    button_primary_border_color_dark="#0071e3",
    button_secondary_background_fill="#e8e8ed",
    button_secondary_background_fill_dark="#000000",
    button_secondary_text_color="#1d1d1f",
    button_secondary_text_color_dark="#f5f5f7",
    button_large_radius="980px",
    button_small_radius="980px",
    checkbox_background_color="#f5f5f7",
    checkbox_background_color_selected="#0071e3",
    checkbox_border_color="#d2d2d7",
    checkbox_border_color_selected="#0071e3",
    checkbox_label_background_fill="#f5f5f7",
    checkbox_label_background_fill_selected="#eaf3fc",
    checkbox_label_border_color="transparent",
    checkbox_label_border_color_selected="transparent",
    checkbox_label_text_color="#1d1d1f",
    checkbox_label_text_color_selected="#1d1d1f",
    slider_color="#0071e3",
    color_accent="#0071e3",
    color_accent_soft="#eaf3fc",
)

CSS = """
:root, html.vivaldi-light {
  --v-bg: #f5f5f7;
  --v-surface: #ffffff;
  --v-surface-2: #f5f5f7;
  --v-input: #f5f5f7;
  --v-output: #fbfbfd;
  --v-line: rgba(0,0,0,0.06);
  --v-text: #1d1d1f;
  --v-muted: #6e6e73;
  --v-foot: #86868b;
  --v-accent: #0071e3;
  --v-accent-hover: #0077ed;
  --v-accent-soft: #eaf3fc;
  --v-link: #0066cc;
  --v-ok: #34c759;
  --v-portal: #ffffff;
  --v-chip-bg: rgba(255,255,255,0.72);
  --v-shadow: 0 2px 12px rgba(0,0,0,0.04);
  --v-shadow-lift: 0 8px 28px rgba(0,0,0,0.08);
  --v-display: "Instrument Serif", "Times New Roman", serif;
  --v-ui: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --v-mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  color-scheme: light;
}

html.vivaldi-dark {
  --v-bg: #000000;
  --v-surface: #000000;
  --v-surface-2: #000000;
  --v-input: #000000;
  --v-output: #000000;
  --v-line: rgba(255,255,255,0.16);
  --v-text: #f5f5f7;
  --v-muted: #a1a1a6;
  --v-foot: #86868b;
  --v-accent: #0a84ff;
  --v-accent-hover: #409cff;
  --v-accent-soft: #001f3f;
  --v-link: #2997ff;
  --v-ok: #30d158;
  --v-portal: #000000;
  --v-chip-bg: rgba(0,0,0,0.55);
  --v-shadow: inset 0 0 0 1px rgba(255,255,255,0.14);
  --v-shadow-lift: inset 0 0 0 1px rgba(255,255,255,0.28);
  color-scheme: dark;
}

/* Light: force readable text even if Gradio injects .dark tokens */
html.vivaldi-light,
html.vivaldi-light .gradio-container,
html.vivaldi-light .gradio-container .main,
html.vivaldi-light label,
html.vivaldi-light .label-wrap,
html.vivaldi-light .label-wrap span,
html.vivaldi-light .block-label,
html.vivaldi-light .block-title,
html.vivaldi-light p,
html.vivaldi-light span,
html.vivaldi-light .prose,
html.vivaldi-light .markdown,
html.vivaldi-light .markdown * {
  color: #1d1d1f !important;
}
html.vivaldi-light .batch-mark,
html.vivaldi-light .hub-title,
html.vivaldi-light .am-command-title,
html.vivaldi-light .yt-loading-title,
html.vivaldi-light .yt-done-title {
  color: #1d1d1f !important;
}
html.vivaldi-light .batch-lede,
html.vivaldi-light .hub-copy,
html.vivaldi-light .am-command-sub,
html.vivaldi-light .batch-foot,
html.vivaldi-light .batch-chip,
html.vivaldi-light .yt-loading-sub,
html.vivaldi-light .yt-done-sub,
html.vivaldi-light .yt-done-kicker,
html.vivaldi-light .yt-item-body small {
  color: #6e6e73 !important;
}
html.vivaldi-light input,
html.vivaldi-light textarea,
html.vivaldi-light select {
  color: #1d1d1f !important;
  -webkit-text-fill-color: #1d1d1f !important;
}
html.vivaldi-light input::placeholder,
html.vivaldi-light textarea::placeholder {
  color: #86868b !important;
  -webkit-text-fill-color: #86868b !important;
  opacity: 1 !important;
}
html.vivaldi-light .hub-arrow,
html.vivaldi-light .batch-back,
html.vivaldi-light a {
  color: #0066cc !important;
}
html.vivaldi-light button.batch-theme-btn,
html.vivaldi-light button.batch-theme-btn span,
html.vivaldi-light button.batch-theme-btn [data-theme-label] {
  background: #e8e8ed !important;
  background-color: #e8e8ed !important;
  color: #0066cc !important;
  -webkit-text-fill-color: #0066cc !important;
}

html.vivaldi-dark,
html.vivaldi-dark .gradio-container,
html.vivaldi-dark label,
html.vivaldi-dark .label-wrap span,
html.vivaldi-dark .block-label,
html.vivaldi-dark p,
html.vivaldi-dark span,
html.vivaldi-dark input,
html.vivaldi-dark textarea {
  color: #f5f5f7 !important;
  -webkit-text-fill-color: #f5f5f7;
}
html.vivaldi-dark .batch-lede,
html.vivaldi-dark .batch-foot,
html.vivaldi-dark .batch-chip,
html.vivaldi-dark .am-command-sub,
html.vivaldi-dark .yt-loading-sub,
html.vivaldi-dark .yt-done-sub,
html.vivaldi-dark .yt-item-body small {
  color: #a1a1a6 !important;
  -webkit-text-fill-color: #a1a1a6;
}
html.vivaldi-dark .batch-theme-btn,
html.vivaldi-dark .hub-arrow,
html.vivaldi-dark .batch-back,
html.vivaldi-dark a {
  color: #2997ff !important;
  -webkit-text-fill-color: #2997ff;
}
html.vivaldi-dark .batch-panel,
html.vivaldi-dark .yt-controls,
html.vivaldi-dark .am-command,
html.vivaldi-dark .am-playlist-strip,
html.vivaldi-dark .fs-season-card,
html.vivaldi-dark .yt-item,
html.vivaldi-dark .batch-progress,
html.vivaldi-dark .gradio-container .block,
html.vivaldi-dark .gradio-container .form,
html.vivaldi-dark .gradio-container .panel-wrap,
html.vivaldi-dark .gradio-container .group,
html.vivaldi-dark .gradio-container .gr-group,
html.vivaldi-dark .gradio-container [class*="block "],
html.vivaldi-dark .yt-studio,
html.vivaldi-dark .yt-form {
  background: #000000 !important;
  background-color: #000000 !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12) !important;
}
html.vivaldi-dark .hub-portal {
  background: #000000 !important;
}
html.vivaldi-dark .gradio-container label:has(input[type="radio"]),
html.vivaldi-dark .gradio-container label:has(input[type="checkbox"]),
html.vivaldi-dark .gradio-container .form > label {
  background: #000000 !important;
  color: #f5f5f7 !important;
  -webkit-text-fill-color: #f5f5f7 !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.16) !important;
}
html.vivaldi-dark .gradio-container label:has(input[type="radio"]:checked),
html.vivaldi-dark .gradio-container label:has(input[type="checkbox"]:checked) {
  background: #001529 !important;
  box-shadow: inset 0 0 0 1.5px #0a84ff !important;
}

/* legacy class from older toggle */
html.batch-light { }

html, body, gradio-app, .gradio-container, .main, .app {
  background: var(--v-bg) !important;
  color: var(--v-text) !important;
  font-family: var(--v-ui) !important;
  -webkit-font-smoothing: antialiased;
  transition: background-color 320ms ease, color 320ms ease;
}

body, gradio-app {
  min-height: 100vh;
  background: var(--v-bg) !important;
}

/* Inputs — keep surfaces readable in both themes */
.gradio-container input[type="text"],
.gradio-container input[readonly],
.gradio-container textarea,
.gradio-container [data-testid="dropdown"] input {
  background: var(--v-input) !important;
  color: var(--v-text) !important;
  border: 0 !important;
  border-radius: 14px !important;
  box-shadow: inset 0 0 0 1px var(--v-line) !important;
}

::selection { background: rgba(0,113,227,0.22); color: var(--v-text); }

.gradio-container,
.gradio-container .main,
.gradio-container .fillable {
  width: 100% !important;
  max-width: 980px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}
.gradio-container { padding: 36px 22px 72px !important; }

footer, .svelte-1sk0pyu, .built-with { display: none !important; }

.batch-shell { animation: v-settle 700ms cubic-bezier(0.22, 1, 0.36, 1) both; }
@keyframes v-settle {
  from { opacity: 0; transform: translateY(10px); filter: blur(6px); }
  to { opacity: 1; transform: none; filter: none; }
}

.batch-hero {
  display: grid; gap: 18px; margin-bottom: 28px; padding-top: 12px;
  text-align: center; justify-items: center; width: 100%;
}
.batch-hero:not(:has(.batch-lede)) { margin-bottom: 20px; }
.batch-top {
  display: grid;
  grid-template-columns: minmax(72px, 1fr) auto minmax(72px, 1fr);
  align-items: center; gap: 12px; width: 100%;
}
.batch-mark {
  font-family: var(--v-display); font-weight: 400; font-style: italic;
  font-size: clamp(2.8rem, 7vw, 4.5rem); letter-spacing: -0.035em;
  line-height: 0.92; color: var(--v-text); margin: 0; text-align: center;
  grid-column: 2;
}
.batch-mark span { color: var(--v-text); font-style: italic; }
.batch-chips {
  display: flex; gap: 8px; flex-wrap: wrap; align-items: center; justify-content: flex-end;
  justify-self: end; grid-column: 3;
}
.batch-back, .batch-back-spacer {
  justify-self: start; grid-column: 1;
}
.batch-back {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 8px 14px; border: 0; border-radius: 980px; cursor: pointer;
  background: transparent; color: var(--v-link) !important;
  font-family: var(--v-ui); font-size: 15px; font-weight: 500;
  letter-spacing: -0.016em; box-shadow: var(--v-shadow);
}
.batch-back:hover { opacity: 0.8; }
.batch-back-spacer { width: 1px; height: 1px; }
.batch-chip {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; border: 0; border-radius: 980px;
  color: var(--v-muted) !important; font-size: 12px; letter-spacing: -0.01em;
  background: transparent !important;
  white-space: nowrap; font-family: var(--v-ui);
  box-shadow: inset 0 0 0 1px var(--v-line);
}
button.batch-theme-btn.batch-theme-btn,
.batch-theme-btn.batch-theme-btn {
  display: inline-flex !important; align-items: center !important; gap: 8px !important;
  padding: 6px 14px !important; border: 0 !important; border-radius: 980px !important;
  cursor: pointer !important; font-family: var(--v-ui) !important;
  font-size: 12px !important; font-weight: 600 !important; letter-spacing: -0.01em !important;
  min-height: auto !important; line-height: 1.2 !important;
  background: #e8e8ed !important; background-color: #e8e8ed !important;
  color: #0066cc !important; -webkit-text-fill-color: #0066cc !important;
  box-shadow: none !important; text-shadow: none !important;
  appearance: none !important; -webkit-appearance: none !important;
}
html.vivaldi-dark button.batch-theme-btn.batch-theme-btn,
html.vivaldi-dark .batch-theme-btn.batch-theme-btn {
  background: #000000 !important; background-color: #000000 !important;
  color: #0a84ff !important; -webkit-text-fill-color: #0a84ff !important;
  box-shadow: inset 0 0 0 1px rgba(10,132,255,0.55) !important;
}
button.batch-theme-btn.batch-theme-btn:hover {
  background: #dbeafe !important; color: #0066cc !important;
  -webkit-text-fill-color: #0066cc !important;
}
html.vivaldi-dark button.batch-theme-btn.batch-theme-btn:hover {
  background: #001529 !important; color: #409cff !important;
  -webkit-text-fill-color: #409cff !important;
}
button.batch-theme-btn span,
button.batch-theme-btn [data-theme-label],
.batch-theme-btn span,
.batch-theme-btn [data-theme-label] {
  color: inherit !important;
  -webkit-text-fill-color: inherit !important;
  background: transparent !important;
}
.batch-chip i {
  width: 7px; height: 7px; border-radius: 50%; background: var(--v-ok);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--v-ok) 20%, transparent);
}
.batch-lede {
  margin: 0 auto; max-width: 36rem; color: var(--v-muted);
  font-size: 21px; line-height: 1.381; font-weight: 400; letter-spacing: 0.011em;
  text-align: center;
}

.batch-panel, .am-command, .am-playlist-strip {
  border: 0 !important;
  background: transparent !important;
  box-shadow: inset 0 0 0 1px var(--v-line) !important;
  border-radius: 28px !important;
}
html.vivaldi-light .batch-panel,
html.vivaldi-light .am-command,
html.vivaldi-light .am-playlist-strip,
html.vivaldi-light .yt-controls {
  background: #ffffff !important;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
}
.batch-panel .label-wrap, .batch-panel label span, .batch-panel .block-label,
.am-command label span, .am-playlist-strip label span {
  font-family: var(--v-ui) !important; font-size: 12px !important;
  letter-spacing: -0.01em !important; text-transform: none !important;
  color: var(--v-muted) !important; font-weight: 600 !important;
}

.gradio-container textarea,
.gradio-container input[type="text"] {
  font-family: var(--v-ui) !important; font-size: 16px !important;
  line-height: 1.4 !important;
  transition: box-shadow 180ms ease, background 180ms ease !important;
}
.gradio-container textarea:focus,
.gradio-container input[type="text"]:focus {
  box-shadow: inset 0 0 0 2px var(--v-accent) !important;
  background: var(--v-surface) !important;
}

.batch-cta button, button.batch-cta {
  width: 100% !important; min-height: 48px !important; border-radius: 980px !important;
  font-family: var(--v-ui) !important; font-weight: 600 !important;
  font-size: 17px !important; letter-spacing: -0.022em !important;
  text-transform: none !important; background: var(--v-accent) !important;
  border: none !important; box-shadow: none !important; color: #fff !important;
  transition: transform 160ms ease, background 160ms ease, opacity 160ms ease !important;
}
.batch-cta button:hover {
  background: var(--v-accent-hover) !important; transform: scale(1.015);
  box-shadow: none !important;
}
.batch-cta.is-running button, button.batch-cta.is-running {
  animation: v-pulse 1.5s ease-in-out infinite; pointer-events: none; opacity: 0.92;
}
@keyframes v-pulse {
  0%, 100% { opacity: 0.88; }
  50% { opacity: 1; }
}

.batch-output,
.batch-output .wrap,
.batch-output [data-testid="textbox"] {
  width: 100% !important;
  flex: 1 1 0 !important;
  min-width: 0 !important;
}
.batch-output textarea {
  display: block !important;
  width: 100% !important;
  box-sizing: border-box !important;
  font-family: var(--v-mono) !important;
  font-size: 13px !important;
  line-height: 1.55 !important;
  min-height: 280px !important;
  height: 280px !important;
  max-height: none !important;
  resize: vertical !important;
  overflow: auto !important;
  background: var(--v-output) !important;
  color: var(--v-text) !important;
  border-radius: 16px !important;
  padding: 14px 16px !important;
  box-shadow: inset 0 0 0 1px var(--v-line) !important;
}
.batch-foot {
  margin-top: 28px; color: var(--v-foot); font-size: 12px; line-height: 1.5;
  letter-spacing: -0.01em; text-align: center; max-width: 42rem; margin-left: auto; margin-right: auto;
}

.batch-progress {
  margin: 16px 0 8px; padding: 18px 20px; border-radius: 22px;
  border: 0; background: var(--v-surface); box-shadow: var(--v-shadow);
  animation: v-settle 480ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
.batch-progress-meta {
  display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px;
  font-family: var(--v-ui); font-size: 13px; color: var(--v-muted); letter-spacing: -0.01em;
}
.batch-progress-meta strong { color: var(--v-text); font-weight: 600; }
.batch-progress-track {
  height: 6px; border-radius: 999px; background: color-mix(in srgb, var(--v-text) 8%, transparent);
  overflow: hidden;
}
.batch-progress-fill {
  height: 100%; width: 0%; border-radius: inherit;
  background: linear-gradient(90deg, #0066cc, #0071e3, #2997ff);
  background-size: 200% 100%;
  transition: width 400ms cubic-bezier(0.22, 1, 0.36, 1);
}
.batch-progress.is-running .batch-progress-fill { animation: v-shimmer 1.3s linear infinite; }
.batch-progress.is-done .batch-progress-fill {
  background: linear-gradient(90deg, #248a3d, #34c759); animation: none;
}
@keyframes v-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

.hub-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin: 18px 0 8px;
}
@media (max-width: 720px) { .hub-grid { grid-template-columns: 1fr; } }

.hub-portal {
  position: relative; overflow: hidden; isolation: isolate;
  display: flex; flex-direction: row; align-items: flex-end; justify-content: space-between;
  gap: 16px; text-align: left; cursor: pointer;
  padding: 28px 30px; min-height: 220px; border-radius: 28px;
  border: 0; background: var(--v-portal);
  box-shadow: var(--v-shadow);
  transition: transform 220ms cubic-bezier(0.22, 1, 0.36, 1), box-shadow 220ms ease;
}
.hub-portal-art {
  position: absolute; inset: -12px; z-index: 0;
  background-size: cover; background-position: center;
  filter: blur(8px) saturate(1.08) brightness(0.95);
  transform: scale(1.05);
  transition: transform 420ms ease, filter 420ms ease;
}
.hub-portal::after {
  content: ""; position: absolute; inset: 0; z-index: 1; border-radius: inherit;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--v-bg) 18%, transparent) 0%,
    color-mix(in srgb, var(--v-bg) 55%, transparent) 45%,
    color-mix(in srgb, var(--v-bg) 82%, transparent) 100%
  );
}
html.vivaldi-dark .hub-portal::after {
  background: linear-gradient(
    180deg,
    rgba(0,0,0,0.15) 0%,
    rgba(0,0,0,0.38) 50%,
    rgba(0,0,0,0.68) 100%
  );
}
html.vivaldi-light .hub-portal::after {
  background: linear-gradient(
    180deg,
    rgba(245,245,247,0.12) 0%,
    rgba(245,245,247,0.38) 50%,
    rgba(245,245,247,0.72) 100%
  );
}
.hub-portal-content {
  position: relative; z-index: 2; width: 100%;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.hub-portal:hover {
  transform: translateY(-3px);
  box-shadow: var(--v-shadow-lift);
}
.hub-portal:hover .hub-portal-art {
  transform: scale(1.08);
  filter: blur(5px) saturate(1.14) brightness(1.02);
}
.hub-portal:hover .hub-arrow { color: var(--v-accent); transform: translateX(4px); }
.hub-kicker, .hub-copy, .hub-go { display: none; }
.hub-title {
  font-family: var(--v-ui); font-size: 32px; font-weight: 600;
  letter-spacing: -0.03em; margin: 0; color: var(--v-text); line-height: 1.05;
  text-shadow: 0 1px 18px color-mix(in srgb, var(--v-bg) 55%, transparent);
}
.hub-arrow {
  font-family: var(--v-ui); font-size: 28px; font-weight: 400;
  color: var(--v-link); line-height: 1; transition: transform 180ms ease, color 180ms ease;
}
.hub-nav-row {
  position: absolute !important; left: -9999px !important; width: 1px !important;
  height: 1px !important; overflow: hidden !important; opacity: 0 !important;
  pointer-events: none !important; margin: 0 !important; padding: 0 !important;
}

/* YouTube studio layout */
.yt-studio { display: flex; flex-direction: column; gap: 14px; width: 100%; }
.yt-studio .yt-controls {
  border: 0 !important;
  background: transparent !important;
  border-radius: 22px !important;
  box-shadow: inset 0 0 0 1px var(--v-line) !important;
  padding: 16px !important;
}
html.vivaldi-light .yt-studio .yt-controls {
  background: #ffffff !important;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
}
.yt-studio .yt-controls > .row {
  display: flex !important;
  gap: 14px !important;
  align-items: stretch !important;
  flex-wrap: wrap !important;
}
.yt-studio .block {
  padding-top: 4px !important;
  padding-bottom: 4px !important;
}
.yt-studio .label-wrap span,
.yt-studio label > span {
  color: var(--v-muted) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
}

.yt-stage { width: 100%; min-height: 420px; }
.yt-loading {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 14px; min-height: 420px; text-align: center;
  animation: v-settle 500ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
.yt-spinner {
  width: 36px; height: 36px; border-radius: 50%;
  border: 2.5px solid color-mix(in srgb, var(--v-text) 12%, transparent);
  border-top-color: var(--v-accent);
  animation: yt-spin 0.85s linear infinite;
}
@keyframes yt-spin { to { transform: rotate(360deg); } }
.yt-loading-title {
  margin: 0; font-family: var(--v-ui); font-size: 28px; font-weight: 600;
  letter-spacing: -0.025em; color: var(--v-text);
}
.yt-loading-sub {
  margin: 0; max-width: 28rem; color: var(--v-muted); font-size: 15px;
  letter-spacing: -0.016em; line-height: 1.4;
}

.yt-done {
  padding: 8px 4px 24px; animation: v-settle 560ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
.yt-done-kicker {
  margin: 0 0 6px; color: var(--v-muted); font-size: 13px; font-weight: 600;
  letter-spacing: -0.01em;
}
.yt-done-title {
  margin: 0 0 6px; font-family: var(--v-ui); font-size: 34px; font-weight: 600;
  letter-spacing: -0.03em; color: var(--v-text); line-height: 1.05;
}
.yt-done-sub {
  margin: 0 0 22px; color: var(--v-foot); font-size: 13px; letter-spacing: -0.01em;
  word-break: break-all;
}
.yt-list {
  list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px;
}
.yt-item {
  display: flex; gap: 14px; align-items: flex-start;
  padding: 16px 18px; border-radius: 18px; background: var(--v-surface);
  box-shadow: var(--v-shadow);
}
.yt-mark {
  width: 28px; height: 28px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 600; flex-shrink: 0; margin-top: 1px;
}
.yt-item.is-ok .yt-mark { background: color-mix(in srgb, var(--v-ok) 18%, transparent); color: var(--v-ok); }
.yt-item.is-fail .yt-mark { background: color-mix(in srgb, #ff453a 18%, transparent); color: #ff453a; }
.yt-item-body { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.yt-item-body strong {
  font-size: 16px; font-weight: 600; letter-spacing: -0.02em; color: var(--v-text);
  line-height: 1.25;
}
.yt-item-body small {
  font-size: 12px; color: var(--v-muted); letter-spacing: -0.01em;
  word-break: break-all; line-height: 1.35;
}

.back-row {
  position: absolute !important; left: -9999px !important; width: 1px !important;
  height: 1px !important; overflow: hidden !important; opacity: 0 !important;
  pointer-events: none !important; margin: 0 !important; padding: 0 !important;
}

.am-command {
  position: relative; z-index: 1;
  margin: 4px 0 18px; padding: 22px 24px;
  background: color-mix(in srgb, var(--v-surface) 82%, transparent) !important;
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
}
.am-command-title {
  font-family: var(--v-ui); font-weight: 600; font-size: 24px;
  letter-spacing: -0.02em; color: var(--v-text); margin: 0 0 4px;
}
.am-command-sub {
  margin: 0 0 14px; color: var(--v-muted); font-size: 15px; line-height: 1.4;
  letter-spacing: -0.016em;
}
.am-section-panel { animation: v-settle 420ms cubic-bezier(0.22, 1, 0.36, 1) both; }
.am-playlist-strip { margin-bottom: 14px; padding: 14px 16px; }
.am-playlist-wrap { margin: 0; padding: 0; }

/* Só a área/estação selecionada — Gradio visible=False + reforço CSS */
.am-studio .am-section-panel[style*="display: none"],
.am-studio .am-playlist-wrap[style*="display: none"],
.am-section-panel[style*="display: none"],
.am-playlist-wrap[style*="display: none"],
.am-section-panel[hidden],
.am-playlist-wrap[hidden] {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
}

/* Segmented Área / Estação */
.am-area-radio {
  margin: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
}
.am-area-radio .wrap,
.am-area-radio .form,
.am-area-radio fieldset,
.am-area-radio > div {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
.am-area-radio label,
.am-area-radio label:has(input[type="radio"]) {
  margin: 0 !important;
  padding: 10px 16px !important;
  border-radius: 980px !important;
  background: var(--v-surface-2) !important;
  color: var(--v-text) !important;
  box-shadow: inset 0 0 0 1px var(--v-line) !important;
  font-family: var(--v-ui) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  letter-spacing: -0.014em !important;
  cursor: pointer !important;
  transition: background 160ms ease, box-shadow 160ms ease, color 160ms ease !important;
}
.am-area-radio label:has(input[type="radio"]:checked) {
  background: var(--v-accent-soft) !important;
  box-shadow: inset 0 0 0 1.5px var(--v-accent) !important;
  color: var(--v-text) !important;
  font-weight: 600 !important;
}
.am-area-radio input[type="radio"] {
  position: absolute !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  pointer-events: none !important;
}

/* Dropdown overlays must beat panels */
.gradio-container [role="listbox"],
.gradio-container ul.options,
.gradio-container .dropdown-content,
.gradio-container .container:has([role="listbox"]) {
  z-index: 9999 !important;
}

/* Four Seasons */
.fs-seasons {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
  margin: 8px 0 18px;
}
@media (max-width: 900px) { .fs-seasons { grid-template-columns: 1fr 1fr; } }
.fs-season-card {
  padding: 18px 16px; border-radius: 22px; background: var(--v-surface);
  box-shadow: var(--v-shadow); text-align: left; min-height: 96px;
}
.fs-season-card .fs-name {
  font-family: var(--v-display); font-style: italic; font-size: 22px;
  color: var(--v-text); margin: 0 0 4px; letter-spacing: -0.02em;
}
.fs-season-card .fs-phase {
  margin: 0; color: var(--v-muted); font-size: 13px; letter-spacing: -0.01em;
}
.fs-season-card[data-s="spring"] { box-shadow: inset 3px 0 0 #34c759, var(--v-shadow); }
.fs-season-card[data-s="summer"] { box-shadow: inset 3px 0 0 #0071e3, var(--v-shadow); }
.fs-season-card[data-s="autumn"] { box-shadow: inset 3px 0 0 #ff9f0a, var(--v-shadow); }
.fs-season-card[data-s="winter"] { box-shadow: inset 3px 0 0 #64d2ff, var(--v-shadow); }
.fs-rack {
  border: 0 !important; background: var(--v-surface) !important;
  border-radius: 28px !important; box-shadow: var(--v-shadow) !important;
  padding: 8px 4px;
}

input[type="range"] { accent-color: var(--v-accent) !important; }

/* Gradio radio / checkbox pills — force Apple light surfaces */
.gradio-container label:has(input[type="radio"]),
.gradio-container label:has(input[type="checkbox"]),
.gradio-container .form > label,
.gradio-container span.svelte-1gfkn6j {
  background: var(--v-surface-2) !important;
  color: var(--v-text) !important;
  border: 0 !important;
  box-shadow: inset 0 0 0 1px var(--v-line) !important;
  border-radius: 12px !important;
}
.gradio-container label:has(input[type="radio"]:checked),
.gradio-container label:has(input[type="checkbox"]:checked) {
  background: var(--v-accent-soft) !important;
  box-shadow: inset 0 0 0 1.5px var(--v-accent) !important;
  color: var(--v-text) !important;
}
.gradio-container .secondary-wrap button,
.gradio-container button.secondary {
  background: var(--v-surface-2) !important;
  color: var(--v-text) !important;
  border: 0 !important;
  border-radius: 980px !important;
  box-shadow: inset 0 0 0 1px var(--v-line) !important;
}
.gradio-container .block {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  overflow: visible !important;
}

@media (max-width: 720px) {
  .batch-hero { padding-top: 8px; }
  .batch-top { grid-template-columns: 1fr; justify-items: center; gap: 10px; }
  .batch-mark, .batch-chips, .batch-back, .batch-back-spacer { grid-column: 1; justify-self: center; }
  .batch-chips { justify-content: center; }
  .batch-mark { font-size: 2.8rem; }
  .batch-lede { font-size: 17px; letter-spacing: -0.016em; }
  .gradio-container { padding: 22px 14px 48px !important; }
  .hub-title { font-size: 26px; }
  .hub-portal { padding: 24px 22px; min-height: 180px; }
}

@media (prefers-reduced-motion: reduce) {
  .batch-shell, .batch-progress, .am-section-panel,
  .batch-cta.is-running button, .batch-progress.is-running .batch-progress-fill {
    animation: none !important;
  }
  .batch-progress-fill, .hub-portal, .hub-portal-art { transition: none !important; }
}
"""

CSS = CSS + "\n" + _hub_art_css()


def progress_html(fraction: float, label: str, *, running: bool = True, done: bool = False) -> str:
    pct = int(max(0.0, min(1.0, fraction)) * 100)
    state = "is-done" if done else ("is-running" if running else "")
    return f"""
<div class="batch-progress {state}">
  <div class="batch-progress-meta">
    <span><strong>{label}</strong></span>
    <span>{pct}%</span>
  </div>
  <div class="batch-progress-track">
    <div class="batch-progress-fill" style="width:{pct}%"></div>
  </div>
</div>
"""


THEME_CHIP = """
<button type="button" class="batch-theme-btn" onclick="toggleBatchTheme()" aria-label="Alternar aparência">
  <span data-theme-label>Claro</span>
</button>
"""
