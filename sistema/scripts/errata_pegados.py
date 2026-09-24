#!/usr/bin/env python3
"""errata_pegados.py — Errata mecanica: separar palabras pegadas por la
conversion original en juntas de anotacion ("2015Establecer" -> "2015 Establecer").

Regla: insertar espacio en el limite [minuscula|digito] + [Mayuscula-accentuada]
cuando ambos lados parecen parte de palabras. El espanol no compone palabras
estilo aleman; un salto a mayusculas a mitad de flujo es artefacto de conversion
(en este corpus). Casos legitimos afectados (p. ej. "kWh") son despreciables en
texto legal, y todo cambio queda en la bitacora y en git (reversible).

Modos:
    --detectar   : cuenta ocurrencias por archivo (no modifica nada)
    --aplicar    : aplica la correccion + escribe bitacora JSONL
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "normas_procesar"
BITACORA = ROOT / "sistema" / "verificacion" / "informes" / "errata-pegados.jsonl"
# minuscula o digito, seguido de MAYUSCULA (incluye acentuadas); no al inicio
# de linea despues de salto (los encabezados "ARTICULO" legitimos van seguidos
# de punto/espacio; el patron exige minuscula|digito ANTES, asi que un heading
# "# Ley 142 de 1994Por" si pegaria y ES artefacto tambien).
PEGADO_RX = re.compile(r"(?<=[a-záéíóúñ0-9])(?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])"
                       r"|(?<=[0-9])(?=[A-ZÁÉÍÓÚÑ]{2,}[a-záéíóúñ])")


def procesar(path: Path, aplicar: bool):
    texto = path.read_text(encoding="utf-8", errors="replace")
    cambios = []
    out = []
    for n, ln in enumerate(texto.split("\n"), 1):
        nuevo = PEGADO_RX.sub(" ", ln)
        if nuevo != ln:
            for m in re.finditer(r"\S+", ln):
                pass
            cambios.append({"linea": n,
                            "antes": ln.strip()[:160],
                            "despues": nuevo.strip()[:160]})
        out.append(nuevo)
    if aplicar and cambios:
        path.write_text("\n".join(out), encoding="utf-8")
    return cambios


def main():
    aplicar = "--aplicar" in sys.argv
    total = 0
    resumen = []
    for p in sorted(CORPUS.glob("*.md")):
        cambios = procesar(p, aplicar)
        if cambios:
            total += len(cambios)
            resumen.append((p.name, len(cambios)))
            if aplicar:
                with open(BITACORA, "a", encoding="utf-8") as fh:
                    for c in cambios:
                        fh.write(json.dumps({"archivo": p.name, **c}, ensure_ascii=False) + "\n")
    modo = "APLICADO" if aplicar else "DETECCION"
    print(f"== {modo}: {total} ocurrencias en {len(resumen)} archivos ==")
    for nombre, n in sorted(resumen, key=lambda x: -x[1]):
        print(f"  {n:>5}  {nombre}")
    sys.exit(0)


if __name__ == "__main__":
    main()
