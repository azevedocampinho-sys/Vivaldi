"""Local-AI playlist intelligence (recommendations, sequencing, curiosities)."""

from __future__ import annotations

import json

from ai import local as llm
from apple_music.client import Playlist, Track


def _track_blob(tracks: list[Track], limit: int = 60) -> str:
    rows = []
    for i, t in enumerate(tracks[:limit], start=1):
        rows.append(
            {
                "n": i,
                "title": t.name,
                "artist": t.artist,
                "album": t.album,
                "year": t.year,
                "genre": t.genre,
            }
        )
    return json.dumps(rows, ensure_ascii=False, indent=2)


def recommend(playlist: Playlist, model: str) -> str:
    system = (
        "Você é um diretor musical no nível das melhores playlists editoriais do Spotify. "
        "Sugira apenas músicas que façam sentido estético/emocional com a playlist. "
        "Responda em português. Para cada sugestão: título, artista, por que encaixa (1 linha). "
        "Não invente ISRC. Se não tiver certeza do ano, omita. Liste 8–12 sugestões. "
        "Nunca incentive download ilegal."
    )
    user = (
        f"Playlist: {playlist.name}\n"
        f"Faixas atuais:\n{_track_blob(playlist.tracks)}\n\n"
        "Indique músicas para complementar (não repetir as que já estão)."
    )
    return llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=model,
        temperature=0.8,
    )


def best_sequence(playlist: Playlist, model: str) -> str:
    system = (
        "Você é um sequencer de playlists. Reordene as faixas para o melhor fluxo: "
        "energia, tom, BPM percebido, arco emocional (abertura → pico → desfecho). "
        "Responda em português com: (1) nova ordem numerada título — artista; "
        "(2) breve racional do arco. Use só as faixas fornecidas, todas elas."
    )
    user = f"Playlist: {playlist.name}\nFaixas:\n{_track_blob(playlist.tracks, limit=80)}"
    return llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=model,
        temperature=0.5,
    )


def ordered_tracks(playlist: Playlist, model: str) -> tuple[list[Track], str]:
    """Ask the local model for a permutation of track indices, then build the list."""
    tracks = playlist.tracks[:80]
    if not tracks:
        return [], "playlist vazia"
    system = (
        "Você reordena playlists. Responda APENAS com JSON válido, sem markdown: "
        '{"order":[n,...],"why":"frase curta"}. '
        "`order` deve listar TODOS os números n das faixas exatamente uma vez "
        "(permutação completa). n começa em 1."
    )
    user = f"Playlist: {playlist.name}\nFaixas:\n{_track_blob(tracks)}"
    raw = llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=model,
        temperature=0.3,
    )
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        payload = json.loads(raw[start : end + 1] if start >= 0 and end > start else raw)
        order = [int(x) for x in payload.get("order") or []]
        why = str(payload.get("why") or "").strip()
    except Exception:  # noqa: BLE001
        return [], f"IA não devolveu JSON utilizável:\n{raw[:500]}"

    n = len(tracks)
    if sorted(order) != list(range(1, n + 1)):
        return [], (
            f"ordem inválida (esperava permutação 1..{n}, recebi {order[:20]}…). "
            f"Resposta: {raw[:400]}"
        )
    ordered = [tracks[i - 1] for i in order]
    # Append any tracks beyond the AI window in original order
    if len(playlist.tracks) > n:
        ordered.extend(playlist.tracks[n:])
    note = why or "sequência gerada pela IA local"
    return ordered, note


def chat_about(
    playlist: Playlist | None,
    question: str,
    history: list[tuple[str, str]],
    model: str,
) -> tuple[str, list[tuple[str, str]]]:
    system = (
        "Você é um companheiro musical culto e direto. Fale sobre artistas, álbuns, "
        "gêneros, eras, cenas e curiosidades. Use português. Se a pergunta for sobre "
        "a playlist carregada, use o contexto. Não invente biografias duvidosas — "
        "indique quando for especulação. Nunca ajude a baixar ou pirater música."
    )
    ctx = ""
    if playlist:
        ctx = f"\nPlaylist ativa: {playlist.name}\n{_track_blob(playlist.tracks, limit=40)}\n"
    messages = [{"role": "system", "content": system + ctx}]
    for q, a in history[-8:]:
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": question.strip()})
    answer = llm.chat(messages, model=model, temperature=0.7)
    history = history + [(question.strip(), answer)]
    return answer, history
