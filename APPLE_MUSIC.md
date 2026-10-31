# Apple Music Studio — setup seguro

## O que este módulo faz
- Lê playlists via **Apple Music API oficial**
- Detecta **duplicatas**
- Filtra por **ano** e **gênero**
- Usa **Ollama no seu M4** para indicações, sequência e chat
- **Grava no Apple Music** (caminho oficial):
  - **Remover duplicatas** → tenta apagar in-place; se a Apple bloquear (comum), cria `Nome · limpa`
  - **Filtro** → cria `Nome · ano/gênero` com o recorte
  - **Melhor sequência** → cria `Nome · sequência` na ordem sugerida pela IA

## Limite da Apple (importante)
A API pública MusicKit **permite criar playlists e adicionar faixas**.
**Não** permite de forma confiável apagar/reordenar faixas numa playlist já existente
(DELETE/PUT costumam voltar 401/403). Por isso o Vivaldi aplica mudanças criando
uma playlist nova na sua biblioteca — ela aparece no app Música em todos os aparelhos
com Biblioteca sincronizada. A original fica intacta.

## O que NÃO faz (anti-ban / anti-ToS)
- Não baixa áudio/DRM
- Não faz scrape de music.apple.com
- Não usa tokens “web” não oficiais para forçar DELETE
- Não dispara requests em rajada (intervalo mínimo + cache + backoff em HTTP 429)

## 1) Conta Apple Developer + MusicKit
1. [developer.apple.com](https://developer.apple.com) → Certificates, Identifiers & Keys
2. Crie uma **Key** com **MusicKit** habilitado
3. Anote **Team ID**, **Key ID** e baixe o `.p8`

## 2) Developer token
```bash
cd yt-batch-downloader
source .venv/bin/activate
python scripts/make_developer_token.py \
  --team-id SEU_TEAM_ID \
  --key-id SEU_KEY_ID \
  --p8 ~/Downloads/AuthKey_XXXXX.p8
```
Cole o JWT em `.env` como `APPLE_MUSIC_DEVELOPER_TOKEN=...`

## 3) Music User Token
Abra no Safari:
`static/musickit_auth.html`

Cole o developer token → **Autorizar com Apple** → copie o user token para
`APPLE_MUSIC_USER_TOKEN=...`

Sem user token, o app só lê demo / não grava.

## 4) IA local no M4
```bash
brew install ollama
ollama serve
```

O Vivaldi escolhe um modelo **estável** e atualiza o digest quando muda.

## 5) Modo demo
Sem tokens, o app usa `sample_data/playlist_demo.json` — zero chamadas à Apple.
Os botões de escrita explicam o que fariam, sem gravar.
