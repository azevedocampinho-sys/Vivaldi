"""Vivaldi — visual system Apple-premium (SF Pro + Interactive Blue + Instrument Serif brand)."""

from __future__ import annotations

import gradio as gr

HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<script>
(function () {
  try {
    var saved = localStorage.getItem("vivaldi-theme");
    if (saved === "dark") document.documentElement.classList.add("vivaldi-dark");
    else document.documentElement.classList.add("vivaldi-light");
  } catch (e) {
    document.documentElement.classList.add("vivaldi-light");
  }
  window.toggleBatchTheme = function () {
    var root = document.documentElement;
    var dark = root.classList.toggle("vivaldi-dark");
    root.classList.toggle("vivaldi-light", !dark);
    try { localStorage.setItem("vivaldi-theme", dark ? "dark" : "light"); } catch (e) {}
    document.querySelectorAll("[data-theme-label]").forEach(function (n) {
      n.textContent = dark ? "Escuro" : "Claro";
    });
  };
  document.addEventListener("DOMContentLoaded", function () {
    var dark = document.documentElement.classList.contains("vivaldi-dark");
    document.querySelectorAll("[data-theme-label]").forEach(function (n) {
      n.textContent = dark ? "Escuro" : "Claro";
    });
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
    background_fill_primary_dark="#1d1d1f",
    background_fill_secondary="#f5f5f7",
    background_fill_secondary_dark="#161617",
    border_color_primary="rgba(0,0,0,0.08)",
    border_color_primary_dark="rgba(255,255,255,0.12)",
    block_background_fill="#ffffff",
    block_background_fill_dark="#1d1d1f",
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
    button_secondary_background_fill_dark="#333336",
    button_secondary_text_color="#1d1d1f",
    button_secondary_text_color_dark="#f5f5f7",
    button_large_radius="980px",
    button_small_radius="980px",
    checkbox_background_color="#f5f5f7",
    checkbox_background_color_selected="#0071e3",
    checkbox_border_color="#d2d2d7",
    checkbox_border_color_selected="#0071e3",
    checkbox_label_background_fill="#ffffff",
    checkbox_label_background_fill_selected="#eef5fd",
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
  --v-surface: #1d1d1f;
  --v-surface-2: #161617;
  --v-input: #000000;
  --v-output: #000000;
  --v-line: rgba(255,255,255,0.12);
  --v-text: #f5f5f7;
  --v-muted: #86868b;
  --v-foot: #6e6e73;
  --v-accent: #0071e3;
  --v-accent-hover: #147ce5;
  --v-accent-soft: #0a2540;
  --v-link: #2997ff;
  --v-ok: #30d158;
  --v-portal: #1d1d1f;
  --v-chip-bg: rgba(29,29,31,0.8);
  --v-shadow: none;
  --v-shadow-lift: 0 8px 32px rgba(0,0,0,0.45);
  color-scheme: dark;
}

/* legacy class from older toggle */
html.batch-light { }

html, body, gradio-app, .gradio-container, .main, .app, .wrap, .contain {
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

/* Dropdown / select controls — never pitch-black in light mode */
.gradio-container .wrap.svelte-1uj8rng,
.gradio-container .container > .wrap,
.gradio-container [data-testid="dropdown"] .wrap,
.gradio-container .dropdown-container,
.gradio-container .secondary-wrap input,
.gradio-container .wrap input[type="text"],
.gradio-container .wrap input[readonly],
.gradio-container .icon-wrap {
  background: var(--v-input) !important;
  color: var(--v-text) !important;
  border-color: transparent !important;
  border-radius: 12px !important;
}
.gradio-container .wrap.svelte-1uj8rng input,
.gradio-container [data-testid="dropdown"] input {
  background: transparent !important;
  color: var(--v-text) !important;
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
  display: grid; gap: 18px; margin-bottom: 28px; padding-top: 28px;
  text-align: center; justify-items: center;
}
.batch-hero:not(:has(.batch-lede)) { margin-bottom: 20px; }
.batch-top {
  display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap;
  width: 100%; position: relative;
}
.batch-mark {
  font-family: var(--v-display); font-weight: 400; font-style: italic;
  font-size: clamp(3.4rem, 9vw, 5.5rem); letter-spacing: -0.035em;
  line-height: 0.92; color: var(--v-text); margin: 0; text-align: center;
}
.batch-mark span { color: var(--v-text); font-style: italic; }
.batch-chips {
  display: flex; gap: 8px; flex-wrap: wrap; align-items: center; justify-content: center;
  position: absolute; right: 0; top: 50%; transform: translateY(-50%);
}
.batch-chip, .batch-theme-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; border: 0; border-radius: 980px;
  color: var(--v-muted) !important; font-size: 12px; letter-spacing: -0.01em;
  background: var(--v-chip-bg) !important;
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  white-space: nowrap; font-family: var(--v-ui); box-shadow: inset 0 0 0 1px var(--v-line);
}
button.batch-theme-btn, .batch-theme-btn {
  cursor: pointer;
  color: var(--v-link) !important;
  background: #ffffff !important;
  font-weight: 500 !important;
  min-height: auto !important;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.12) !important;
  transition: background 160ms ease, color 160ms ease;
}
html.vivaldi-dark button.batch-theme-btn,
html.vivaldi-dark .batch-theme-btn {
  color: #2997ff !important;
  background: #1d1d1f !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.18) !important;
}
button.batch-theme-btn:hover, .batch-theme-btn:hover {
  background: var(--v-accent-soft) !important;
  color: var(--v-link) !important;
}
button.batch-theme-btn span, .batch-theme-btn [data-theme-label] {
  color: inherit !important;
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
  background: var(--v-surface) !important;
  box-shadow: var(--v-shadow) !important;
  border-radius: 28px !important;
}
.batch-panel .label-wrap, .batch-panel label span, .batch-panel .block-label,
.am-command label span, .am-playlist-strip label span {
  font-family: var(--v-ui) !important; font-size: 12px !important;
  letter-spacing: -0.01em !important; text-transform: none !important;
  color: var(--v-muted) !important; font-weight: 600 !important;
}

textarea, input[type="text"], .wrap textarea, .wrap input {
  font-family: var(--v-ui) !important; font-size: 17px !important;
  line-height: 1.35 !important; border-radius: 16px !important;
  background: var(--v-input) !important; color: var(--v-text) !important;
  border: 0 !important; box-shadow: inset 0 0 0 1px transparent !important;
  transition: box-shadow 180ms ease, background 180ms ease !important;
}
textarea:focus, input[type="text"]:focus {
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

.batch-output textarea {
  font-family: var(--v-mono) !important; font-size: 13px !important;
  line-height: 1.55 !important; min-height: 260px !important;
  background: var(--v-output) !important; color: var(--v-text) !important;
  border-radius: 18px !important;
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
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 12px 0 22px;
}
@media (max-width: 1100px) { .hub-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 720px) { .hub-grid { grid-template-columns: 1fr; } }

.hub-portal {
  display: flex; flex-direction: column; gap: 12px; text-align: left;
  padding: 36px 30px 28px; min-height: 240px; border-radius: 28px;
  border: 0; background: var(--v-portal);
  box-shadow: var(--v-shadow);
  transition: transform 220ms cubic-bezier(0.22, 1, 0.36, 1), box-shadow 220ms ease;
}
.hub-portal:hover {
  transform: translateY(-4px);
  box-shadow: var(--v-shadow-lift);
}
.hub-kicker { display: none; }
.hub-title {
  font-family: var(--v-ui); font-size: 32px; font-weight: 600;
  letter-spacing: -0.025em; margin: 0; color: var(--v-text); line-height: 1.05;
}
.hub-copy {
  margin: 0; color: var(--v-muted); font-size: 17px; line-height: 1.35;
  letter-spacing: -0.022em; flex: 1;
}
.hub-go { display: none; }

.back-row button {
  background: var(--v-surface) !important; border: 0 !important;
  color: var(--v-link) !important; border-radius: 980px !important;
  min-height: 34px !important; padding: 0 16px !important;
  font-size: 14px !important; letter-spacing: -0.016em !important;
  text-transform: none !important; font-weight: 500 !important;
  box-shadow: var(--v-shadow) !important;
}
.back-row button:hover { opacity: 0.85 !important; }

.am-command {
  position: sticky; top: 10px; z-index: 40;
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
}
.gradio-container .padded { padding: 4px 0 !important; }

@media (max-width: 720px) {
  .batch-hero { padding-top: 12px; }
  .batch-chips { position: static; transform: none; width: 100%; justify-content: center; }
  .batch-theme-btn:hover { transform: none; }
  .batch-mark { font-size: 3rem; }
  .batch-lede { font-size: 17px; letter-spacing: -0.016em; }
  .gradio-container { padding: 22px 14px 48px !important; }
  .hub-title { font-size: 26px; }
  .hub-portal { min-height: 0; padding: 28px 24px; }
}

@media (prefers-reduced-motion: reduce) {
  .batch-shell, .batch-progress, .am-section-panel,
  .batch-cta.is-running button, .batch-progress.is-running .batch-progress-fill {
    animation: none !important;
  }
  .batch-progress-fill, .hub-portal { transition: none !important; }
}
"""


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
