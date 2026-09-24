#!/usr/bin/env python3
"""Genera normas_procesar/manifest.json: SHA-256 por archivo + hash de conjunto.

El set_hash resume el estado completo del corpus en un solo valor: cambia si
cualquier archivo cambia, se elimina o se agrega. Es el sello contra el que
integrity_check.py verifica antes de cada corrida sensible.
"""
import hashlib
import json

from corpus_config import MANIFEST_PATH, ROOT, corpus_files, iso_now, sha256_file


def compute_manifest() -> dict:
    files = corpus_files()
    if not files:
        raise SystemExit("ERROR: no hay archivos .md en el corpus")
    entries = {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in files}
    set_src = "".join(f"{n}:{entries[n]['sha256']}\n" for n in sorted(entries))
    return {
        "format_version": 1,
        "algorithm": "sha256",
        "scope": "normas_procesar/*.md (primer nivel)",
        "created_at": iso_now(),
        "file_count": len(entries),
        "total_bytes": sum(e["bytes"] for e in entries.values()),
        "set_hash": hashlib.sha256(set_src.encode("utf-8")).hexdigest(),
        "files": entries,
    }


def main() -> None:
    m = compute_manifest()
    MANIFEST_PATH.write_text(
        json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"OK | {m['file_count']} archivos | {m['total_bytes']:,} bytes")
    print(f"set_hash: {m['set_hash']}")
    print(f"Manifiesto: {MANIFEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
