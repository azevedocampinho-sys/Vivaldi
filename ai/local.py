"""Local LLM via Ollama (Apple Silicon / M4). Auto-atualiza tags estáveis quando há digest novo."""

from __future__ import annotations

import json
import os
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Iterator

DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

# Escada de modelos estáveis e leves o bastante para M4 (tag pinada > latest solto).
# O sistema sobe na lista se o preferido não existir; sempre revalida digest no registry.
PREFERRED_STABLE: list[str] = [
    "llama3.2:3b",
    "llama3.2:latest",
    "gemma2:2b",
    "qwen2.5:3b",
    "phi3:mini",
]

DEFAULT_MODEL = PREFERRED_STABLE[0]

ProgressCb = Callable[[str], None]


@dataclass
class ModelInfo:
    name: str
    digest: str
    size: int = 0
    modified_at: str = ""


@dataclass
class EnsureResult:
    model: str
    updated: bool
    pulled: bool
    message: str
    online: bool


def _http_json(url: str, *, data: dict | None = None, timeout: float = 30.0) -> dict[str, Any]:
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def ollama_available(host: str = DEFAULT_HOST) -> bool:
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=1.5) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


def ollama_version(host: str = DEFAULT_HOST) -> str:
    try:
        return str(_http_json(f"{host}/api/version", timeout=2.0).get("version") or "?")
    except Exception:  # noqa: BLE001
        return "?"


def list_models(host: str = DEFAULT_HOST) -> list[str]:
    return [m.name for m in list_models_detailed(host)]


def list_models_detailed(host: str = DEFAULT_HOST) -> list[ModelInfo]:
    try:
        data = _http_json(f"{host}/api/tags", timeout=3.0)
    except Exception:  # noqa: BLE001
        return []
    out: list[ModelInfo] = []
    for m in data.get("models") or []:
        name = (m.get("name") or "").strip()
        if not name:
            continue
        out.append(
            ModelInfo(
                name=name,
                digest=(m.get("digest") or "").strip(),
                size=int(m.get("size") or 0),
                modified_at=str(m.get("modified_at") or ""),
            )
        )
    return out


def _split_model_tag(model: str) -> tuple[str, str]:
    model = model.strip()
    if ":" in model:
        name, tag = model.split(":", 1)
        return name, tag or "latest"
    return model, "latest"


def normalize_name(model: str) -> str:
    name, tag = _split_model_tag(model)
    return f"{name}:{tag}"


def remote_digest(model: str, timeout: float = 12.0) -> str | None:
    """Digest do manifest no registry oficial (sem baixar pesos)."""
    name, tag = _split_model_tag(model)
    # library models live under library/<name>
    url = f"https://registry.ollama.ai/v2/library/{name}/manifests/{tag}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.docker.distribution.v2+json, application/vnd.oci.image.manifest.v1+json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001
        return None

    # Prefer config digest; fallback to first model layer
    cfg = (data.get("config") or {}).get("digest")
    if cfg:
        return str(cfg).replace("sha256:", "")
    layers = data.get("layers") or []
    for layer in layers:
        dig = layer.get("digest")
        if dig and "model" in str(layer.get("mediaType") or ""):
            return str(dig).replace("sha256:", "")
    if layers and layers[0].get("digest"):
        return str(layers[0]["digest"]).replace("sha256:", "")
    return None


def local_digest(model: str, host: str = DEFAULT_HOST) -> str | None:
    want = normalize_name(model)
    base, tag = _split_model_tag(model)
    for info in list_models_detailed(host):
        n = info.name
        if n == want or n == model or n == f"{base}:latest" and tag == "latest":
            return info.digest.replace("sha256:", "") if info.digest else None
        # ollama sometimes lists without :latest
        if ":" not in n and n == base and tag == "latest":
            return info.digest.replace("sha256:", "") if info.digest else None
    return None


def digests_match(local: str | None, remote: str | None) -> bool:
    if not local or not remote:
        return False
    a = local.replace("sha256:", "").lower()
    b = remote.replace("sha256:", "").lower()
    # registry config digest vs local model digest can differ in prefix length —
    # treat equal or either as prefix of the other as match when >= 12 chars
    if a == b:
        return True
    if len(a) >= 12 and len(b) >= 12 and (a.startswith(b) or b.startswith(a)):
        return True
    return False


def is_update_available(model: str, host: str = DEFAULT_HOST) -> bool | None:
    """True = update disponível, False = ok, None = não deu para checar remoto."""
    loc = local_digest(model, host)
    if not loc:
        return True  # precisa baixar
    rem = remote_digest(model)
    if rem is None:
        return None
    return not digests_match(loc, rem)


def pull_model(
    model: str,
    *,
    host: str = DEFAULT_HOST,
    on_progress: ProgressCb | None = None,
) -> Iterator[str]:
    """Faz pull (atualiza se já existe). Yielda linhas de status."""
    payload = json.dumps({"model": model, "stream": True}).encode()
    req = urllib.request.Request(
        f"{host}/api/pull",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for raw in resp:
                line = raw.decode().strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                status = str(evt.get("status") or "")
                total = evt.get("total") or 0
                completed = evt.get("completed") or 0
                if total and completed is not None:
                    pct = int(100 * completed / total) if total else 0
                    msg = f"{status} · {pct}%"
                else:
                    msg = status or line
                if on_progress:
                    on_progress(msg)
                yield msg
                if status == "success":
                    break
    except urllib.error.URLError as exc:
        yield f"erro no pull: {exc}"
    except Exception as exc:  # noqa: BLE001
        yield f"erro no pull: {exc}"


def pull_model_blocking(model: str, host: str = DEFAULT_HOST) -> str:
    last = "…"
    for msg in pull_model(model, host=host):
        last = msg
    return last


def resolve_preferred_model(host: str = DEFAULT_HOST) -> str:
    """Escolhe o melhor modelo estável: preferido da escada se instalado, senão o topo."""
    installed = {normalize_name(m) for m in list_models(host)}
    for pref in PREFERRED_STABLE:
        if normalize_name(pref) in installed:
            return normalize_name(pref)
        base, _ = _split_model_tag(pref)
        # ex.: tem llama3.2:latest e preferimos llama3.2:3b — ainda assim prioriza pref
        if any(normalize_name(pref) == n or n.startswith(f"{base}:") for n in installed):
            # se a tag exata não está, mas a família sim, usa a instalada da família
            for n in sorted(installed):
                if n.startswith(f"{base}:"):
                    return n
    # nada instalado → topo da escada (vai puxar)
    return normalize_name(PREFERRED_STABLE[0])


def ensure_stable_model(
    model: str | None = None,
    *,
    host: str = DEFAULT_HOST,
    auto_update: bool = True,
    on_progress: ProgressCb | None = None,
) -> EnsureResult:
    """Garante modelo estável local e atualiza se o registry tiver digest novo."""
    if not ollama_available(host):
        hint = "brew install ollama && ollama serve" if not shutil.which("ollama") else "ollama serve"
        return EnsureResult(
            model=normalize_name(model or DEFAULT_MODEL),
            updated=False,
            pulled=False,
            online=False,
            message=f"Ollama offline · {hint}",
        )

    target = normalize_name(model or resolve_preferred_model(host))
    before = local_digest(target, host)
    needs: bool | None
    if before is None:
        needs = True
        reason = "não instalado"
    elif not auto_update:
        needs = False
        reason = "ok"
    else:
        rem = remote_digest(target)
        if rem is None:
            # sem registry: tenta pull leve mesmo assim (Ollama no-op se igual)
            needs = True
            reason = "checando via pull"
        elif digests_match(before, rem):
            return EnsureResult(
                model=target,
                updated=False,
                pulled=False,
                online=True,
                message=f"{target} · já na versão estável atual (ollama {ollama_version(host)})",
            )
        else:
            needs = True
            reason = "digest remoto diferente"

    if not needs:
        return EnsureResult(
            model=target,
            updated=False,
            pulled=False,
            online=True,
            message=f"{target} · atual",
        )

    if on_progress:
        on_progress(f"atualizando {target} ({reason})…")
    last = "…"
    for msg in pull_model(target, host=host, on_progress=on_progress):
        last = msg
    after = local_digest(target, host)
    updated = bool(after and after != before)
    pulled = before is None or updated or "success" in last.lower()
    if before is None and after:
        msg = f"{target} · baixado · pronto"
    elif updated:
        msg = f"{target} · atualizado para versão estável nova"
    elif "success" in last.lower():
        msg = f"{target} · confirmado atual (sem mudanças)"
    else:
        msg = f"{target} · {last}"
    return EnsureResult(
        model=target,
        updated=updated,
        pulled=pulled,
        online=True,
        message=msg,
    )


def status_report(host: str = DEFAULT_HOST) -> str:
    if not ollama_available(host):
        return "IA local · ollama offline"
    models = list_models(host)
    preferred = resolve_preferred_model(host)
    upd = is_update_available(preferred, host)
    if upd is True:
        flag = "update disponível"
    elif upd is False:
        flag = "estável atual"
    else:
        flag = "registry indisponível"
    names = ", ".join(models[:5]) if models else "(nenhum)"
    return (
        f"IA local · ollama {ollama_version(host)} online · "
        f"preferido {preferred} ({flag}) · instalados: {names}"
    )


def chat(
    messages: list[dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_HOST,
    temperature: float = 0.7,
    auto_ensure: bool = True,
) -> str:
    if auto_ensure and ollama_available(host):
        # só puxa se faltar localmente; updates agendados ficam no ensure explícito
        if local_digest(model, host) is None:
            ensure_stable_model(model, host=host, auto_update=True)

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode())
        return (data.get("message") or {}).get("content") or "(sem resposta)"
    except urllib.error.URLError as exc:
        return (
            "IA local indisponível. No Terminal:\n"
            "  brew install ollama\n"
            "  ollama serve\n"
            f"  ollama pull {model}\n"
            f"Detalhe: {exc}"
        )
    except Exception as exc:  # noqa: BLE001
        return f"Erro na IA local: {exc}"
