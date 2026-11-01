# Vivaldi

Estúdio local de mídia no Mac (Gradio · localhost).

1. **YouTube** — download em lote (MP4/MP3 + resolução)
2. **Apple Music** — duplicatas, filtros, IA local; grava playlists limpas via API oficial
3. **Stems** — HTDemucs local (instrumental / stems)
4. **Four Seasons** — criação musical em 4 estações (pré → pós), referências da playlist, CIFRA + partitura ABC
5. **ZIP** — anexa .zip / .tar.gz / .gz e descompacta localmente em `zip_out/`

## Rodar

```bash
./run.sh
```

Abre [http://127.0.0.1:7860](http://127.0.0.1:7860).

## Requisitos
- Python 3.12 (`brew install python@3.12`)
- `ffmpeg` (`brew install ffmpeg`) — YouTube
- Opcional Apple Music: ver [APPLE_MUSIC.md](APPLE_MUSIC.md)
- Opcional IA / Four Seasons: `brew install ollama` (o app sobe com `brew services start ollama` se estiver offline)
- Opcional Stems: pesos do Demucs baixam na 1ª execução (PyTorch)

## Docs
- [APPLE_MUSIC.md](APPLE_MUSIC.md) · [STEMS.md](STEMS.md) · [FOUR_SEASONS.md](FOUR_SEASONS.md) · [DESIGN.md](DESIGN.md)
