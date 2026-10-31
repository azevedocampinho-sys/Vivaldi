#!/usr/bin/env python3
"""Garante/atualiza o modelo estável preferido no Ollama."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai import local as llm  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Atualiza modelo estável Ollama se houver digest novo")
    p.add_argument("--model", default="", help="Modelo (default: escada preferida)")
    p.add_argument("--no-update", action="store_true", help="Só resolve, não puxa")
    args = p.parse_args()

    def progress(msg: str) -> None:
        print(msg, flush=True)

    result = llm.ensure_stable_model(
        args.model or None,
        auto_update=not args.no_update,
        on_progress=progress,
    )
    print(result.message)
    print(f"model={result.model} updated={result.updated} online={result.online}")
    return 0 if result.online or not args.model else 1


if __name__ == "__main__":
    raise SystemExit(main())
