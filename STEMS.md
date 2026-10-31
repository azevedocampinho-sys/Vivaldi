# Stems — HTDemucs local

Separação de áudio 100% no Mac (Demucs / Hybrid Transformer Demucs).

## Modos
- **Instrumental rápido** — `vocals` + `no_vocals` (copia `*__instrumental.wav`)
- **Stems completos** — `vocals`, `bass`, `drums`, `other`

## Modelos
| Modelo | Notas |
|--------|--------|
| `htdemucs` | Padrão — bom equilíbrio |
| `htdemucs_ft` | Fine-tuned — mais qualidade, mais lento |
| `htdemucs_6s` | Até 6 stems |
| `mdx_extra` | Alternativa MDX |

## Setup
```bash
source .venv/bin/activate
pip install demucs torch torchaudio
```

Na primeira corrida o Demucs baixa os pesos do modelo.

No M4 tenta **MPS**; se falhar, o Vivaldi refaz em **CPU** automaticamente.

## Uso
Hub → **Stems** → envie um áudio → Separar stems → pasta `stems_out/`.
