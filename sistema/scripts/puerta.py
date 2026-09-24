#!/usr/bin/env python3
"""La puerta: ejecucion ordenada de todas las verificaciones (runner del plan).

Cadena de confianza completa, en orden, deteniendose en el primer fallo
(fail-closed): no tiene sentido medir con el oro un indice podrido, ni
generar artefactos sobre una fuente inconsistente.

  1. integrity_check   — el corpus no fue alterado (sello del paso 1)
  2. differential_check— el indice es fiel al corpus (100% en sus 3 chequeos)
  3. oro_check         — la regla de medir es verdad (set de oro del paso 4)
  4. NP --validate     — la fuente unica del procesador es consistente
  5. NP --check-narrativos — los documentos manuales no mienten (exit 1 si hay issues)

Uso: python3 puerta.py [--solo etapa1,etapa2]   (desde cualquier directorio)
Exit 0 = toda la cadena en verde; exit 1 = primera etapa roja.
"""
import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
PY = sys.executable

ETAPAS = [
    ("integridad", [PY, os.path.join(SCRIPT_DIR, "integrity_check.py")]),
    ("diferencial", [PY, os.path.join(SCRIPT_DIR, "differential_check.py")]),
    ("oro", [PY, os.path.join(SCRIPT_DIR, "oro_check.py")]),
    ("np-ssot", [PY, os.path.join(ROOT, "procesador", "v1.0.0-beta.1", "scripts", "generador.py"), "--validate"]),
    ("np-narrativos", [PY, os.path.join(ROOT, "procesador", "v1.0.0-beta.1", "scripts", "generador.py"), "--check-narrativos"]),
]


def main():
    ap = argparse.ArgumentParser(description="Puerta: cadena completa de verificaciones")
    ap.add_argument("--solo", default=None, help="Solo estas etapas, separadas por coma")
    args = ap.parse_args()

    etapas = ETAPAS
    if args.solo:
        queridas = set(args.solo.split(","))
        etapas = [e for e in ETAPAS if e[0] in queridas]
        desconocidas = queridas - {e[0] for e in etapas}
        if desconocidas:
            print(f"Etapa(s) desconocida(s): {sorted(desconocidas)}")
            sys.exit(2)

    print("=== LA PUERTA: cadena de verificaciones ===")
    print(f"Etapa(s): {', '.join(n for n, _ in etapas)}\n")
    for nombre, cmd in etapas:
        print(f"--- [{nombre}] ---")
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print(f"\nPUERTA CERRADA en '{nombre}' (exit {r.returncode}). "
                  f"Nada de aguas abajo se ejecuta ni se aprueba.")
            sys.exit(1)
        print(f"[{nombre}] OK\n")
    print("PUERTA ABIERTA: corpus íntegro, índice fiel, oro verdadero, fuente consistente.")


if __name__ == "__main__":
    main()
