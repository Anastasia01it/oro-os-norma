#!/usr/bin/env python3
"""Verifica la integridad del corpus contra el manifiesto (control anti-inyección/ítem 29).

Exit 0: corpus íntegro. Exit 1: agregados, eliminados o modificados detectados.
Uso obligatorio antes de corridas sensibles (piloto, lotes) y después de tocar el corpus.
"""
import json
import sys

from build_manifest import compute_manifest
from corpus_config import MANIFEST_PATH


def main() -> None:
    if not MANIFEST_PATH.exists():
        print("ERROR: no existe el manifiesto. Ejecute primero build_manifest.py")
        sys.exit(1)
    stored = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    current = compute_manifest()
    s_files, c_files = stored["files"], current["files"]
    added = sorted(set(c_files) - set(s_files))
    removed = sorted(set(s_files) - set(c_files))
    modified = sorted(
        n for n in set(s_files) & set(c_files) if s_files[n]["sha256"] != c_files[n]["sha256"]
    )
    if added or removed or modified:
        print("ALERTA DE INTEGRIDAD: el corpus diverge del manifiesto.")
        for tag, lst in (("AGREGADOS", added), ("ELIMINADOS", removed), ("MODIFICADOS", modified)):
            for n in lst:
                print(f"  [{tag[:-2]}] {n}")
        print("Acción: revisar cambios y, si son legítimos, regenerar manifiesto (build_manifest.py).")
        sys.exit(1)
    print(f"INTEGRIDAD OK | {current['file_count']} archivos | set_hash {current['set_hash'][:16]}…")


if __name__ == "__main__":
    main()
