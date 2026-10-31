#!/usr/bin/env python3
"""Gera APPLE_MUSIC_DEVELOPER_TOKEN (JWT ES256) a partir da chave .p8 da Apple."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import jwt


def main() -> None:
    p = argparse.ArgumentParser(description="Gera developer token Apple Music")
    p.add_argument("--team-id", required=True, help="Team ID (10 chars)")
    p.add_argument("--key-id", required=True, help="Key ID (10 chars)")
    p.add_argument("--p8", required=True, type=Path, help="Caminho do AuthKey_XXXXX.p8")
    p.add_argument("--days", type=int, default=180, help="Validade (máx ~180)")
    args = p.parse_args()

    private_key = args.p8.read_text(encoding="utf-8")
    now = int(time.time())
    exp = now + min(args.days, 180) * 24 * 3600
    token = jwt.encode(
        {"iss": args.team_id, "iat": now, "exp": exp},
        private_key,
        algorithm="ES256",
        headers={"alg": "ES256", "kid": args.key_id},
    )
    print(token)


if __name__ == "__main__":
    main()
