"""Local Ollama composer for Four Seasons (M4)."""

from __future__ import annotations

import json
import re
from typing import Any

from ai import local as llm
from four_seasons import instruments as inst_cat
from four_seasons.session import Layer, Project


def _system(project: Project) -> str:
    return (
        "Você é o diretor musical do Vivaldi Four Seasons, rodando local no Apple Silicon. "
        "Fases: Primavera=pré-produção, Verão=produção, Outono=arranjo, Inverno=pós. "
        "Respeite as referências Apple Music do usuário (clima/artista/gênero), "
        "sem copiar melodias protegidas. Responda em português. "
        "Quando pedir JSON, devolva só JSON válido.\n\n"
        f"Projeto: {project.title}\n"
        f"Conceito: {project.concept}\n"
        f"Mood: {project.mood}\n"
        f"Tom/modo: {project.key} {project.mode} · {project.tempo_bpm} BPM\n"
        f"Estação: {project.season}\n"
        f"Cantarolar: {project.humming_notes or '—'}\n"
        f"Estrutura: {project.structure or '—'}\n"
        f"Camadas:\n{project.layers_blob()}\n\n"
        f"{project.reference_summary or 'Sem playlist ainda.'}\n"
    )


def spring_brief(project: Project, model: str) -> str:
    user = (
        "Fase PRIMAVERA (pré-produção). Com base no conceito, mood e referências Apple Music, "
        "entregue: (1) brief criativo em 6–10 linhas; (2) sugestão de tom/BPM se ainda fracos; "
        "(3) arco emocional da música; (4) 4–6 referências internas citando artistas/faixas "
        "da playlist do usuário (só clima, sem plagiar)."
    )
    return llm.chat(
        [{"role": "system", "content": _system(project)}, {"role": "user", "content": user}],
        model=model,
        temperature=0.7,
    )


def summer_produce(project: Project, model: str) -> tuple[str, list[Layer]]:
    """Generate / refresh layer ideas for current instruments (+ structure)."""
    if not project.layers:
        # Seed a sensible starter rack
        for iid in ("vocals", "piano", "bass", "drums"):
            meta = inst_cat.BY_ID[iid]
            project.layers.append(
                Layer(
                    id=f"L{len(project.layers)+1}_{iid}",
                    instrument_id=iid,
                    instrument_name=meta.name,
                )
            )

    user = (
        "Fase VERÃO (produção). Gere JSON com este schema:\n"
        '{"structure":"Intro/Verso/…","layers":[{"instrument_id":"…","notes":"…","chords":"C | Am | F | G",'
        '"cifra":"texto cifra","abc":"X:1\\nT:…\\nK:C\\n|…|"}]}\n'
        "Inclua TODAS as camadas atuais (mesmo instrument_id). "
        "cifra e abc por instrumento. Use o cantarolar e as referências Apple Music."
    )
    raw = llm.chat(
        [{"role": "system", "content": _system(project)}, {"role": "user", "content": user}],
        model=model,
        temperature=0.55,
    )
    data = _parse_json(raw)
    narrative = raw
    if not data:
        return f"Produção (texto livre — JSON incompleto):\n{raw}", project.layers

    if data.get("structure"):
        project.structure = str(data["structure"])
    by_id = {layer.instrument_id: layer for layer in project.layers}
    for item in data.get("layers") or []:
        iid = str(item.get("instrument_id") or "")
        layer = by_id.get(iid)
        if not layer:
            continue
        layer.notes = str(item.get("notes") or layer.notes)
        layer.chords = str(item.get("chords") or layer.chords)
        layer.cifra = str(item.get("cifra") or layer.cifra)
        layer.abc = str(item.get("abc") or layer.abc).replace("\\n", "\n")
    narrative = (
        f"Estrutura: {project.structure}\n\n"
        f"Camadas atualizadas:\n{project.layers_blob()}\n\n"
        f"(raw IA)\n{raw[:1200]}"
    )
    return narrative, project.layers


def autumn_chat(
    project: Project,
    message: str,
    history: list[tuple[str, str]],
    model: str,
) -> tuple[str, list[tuple[str, str]], list[Layer]]:
    user = (
        "Fase OUTONO (arranjo/edição). O usuário pede ajustes nas camadas. "
        "Exemplos: inspirar-se em artista/faixa da playlist, mudar groove, "
        "abrir harmonia, silenciar instrumento, etc.\n"
        "Responda com: (1) parágrafo curto do que mudou; (2) JSON opcional "
        '{"layers":[{"instrument_id":"…","notes":"…","chords":"…","muted":false,'
        '"cifra":"…","abc":"…"}]}\n\n'
        f"Pedido: {message.strip()}"
    )
    messages = [{"role": "system", "content": _system(project)}]
    for q, a in history[-6:]:
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": user})
    answer = llm.chat(messages, model=model, temperature=0.65)
    data = _parse_json(answer)
    if data and data.get("layers"):
        by_id = {layer.instrument_id: layer for layer in project.layers}
        for item in data["layers"]:
            iid = str(item.get("instrument_id") or "")
            layer = by_id.get(iid)
            if not layer:
                # allow creating via chat if instrument known
                if iid in inst_cat.BY_ID:
                    meta = inst_cat.BY_ID[iid]
                    layer = Layer(
                        id=f"L{len(project.layers)+1}_{iid}",
                        instrument_id=iid,
                        instrument_name=meta.name,
                    )
                    project.layers.append(layer)
                    by_id[iid] = layer
                else:
                    continue
            if "notes" in item:
                layer.notes = str(item["notes"])
            if "chords" in item:
                layer.chords = str(item["chords"])
            if "muted" in item:
                layer.muted = bool(item["muted"])
            if "cifra" in item:
                layer.cifra = str(item["cifra"])
            if "abc" in item:
                layer.abc = str(item["abc"]).replace("\\n", "\n")
    history = history + [(message.strip(), answer)]
    project.chat_log = history
    return answer, history, project.layers


def winter_finish(project: Project, model: str) -> str:
    user = (
        "Fase INVERNO (pós-produção). Entregue: checklist de mix (8 itens), "
        "notas de master leves para M4/local, e revisão das cifras/partituras "
        "por instrumento (aponta lacunas). Não invente stems de áudio."
    )
    text = llm.chat(
        [{"role": "system", "content": _system(project)}, {"role": "user", "content": user}],
        model=model,
        temperature=0.5,
    )
    project.mix_notes = text
    return text


def _parse_json(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            return None
        blob = raw[start : end + 1]
        # tolerate trailing commas lightly
        blob = re.sub(r",\s*}", "}", blob)
        blob = re.sub(r",\s*]", "]", blob)
        data = json.loads(blob)
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None
