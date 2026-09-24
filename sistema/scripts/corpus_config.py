#!/usr/bin/env python3
"""Configuración compartida del sistema de corpus.

Alineación con plan-estructural/SOLUCION-PLAN-ESTRUCTURAL.md:
- Índice SQLite FTS5 (decisión métrica, SOLUCION §1: comparación resuelta).
- Manifiesto SHA-256: sello de integridad del corpus (ítems 2, 16, 21 y 29 del plan).

Convención: corpus = normas_procesar/*.md (90 normas, ~21 MB).
Cero dependencias externas: solo stdlib Python (criterio S de la métrica).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "normas_procesar"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"
DB_DIR = ROOT / "sistema" / "data"
DB_PATH = DB_DIR / "corpus.index.sqlite"
BOGOTA = timezone(timedelta(hours=-5))


def iso_now() -> str:
    return datetime.now(BOGOTA).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_text_lossless(path: Path) -> tuple[str, str]:
    """Devuelve (texto, encoding) tal que texto.encode(encoding) == bytes originales."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1"


def corpus_files() -> list[Path]:
    return sorted(p for p in CORPUS_DIR.glob("*.md") if p.is_file())
