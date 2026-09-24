#!/usr/bin/env python3
r"""Control diferencial del índice (prueba del plan, ítem 21: GIGO / calidad de recuperación).

Cadena de garantías del corpus:
  archivos ⇄ chunks   (B: reconstrucción byte-por-byte, SHA-256)
  chunks   ⇄ FTS5     (C1: igualdad de conjuntos contra fuerza bruta)
  FTS5     ⊆ rg       (C2: supraconjunto con motor independiente)

A. COBERTURA: índice == disco == manifiesto (mismos archivos).
B. RECONSTRUCCIÓN lossless: cada archivo se reproduce byte-por-byte desde sus chunks.
C1. IGUALDAD EXACTA: sobre muestra sembrada (Random(42)), para triples de tokens
    raros (df 1..8 según rg) y alfabéticos (len >= 6):
        archivos(FTS5 'w1 AND w2 AND w3')
        == archivos(barrido por fuerza bruta de la tabla chunks con tokenizador
           de referencia: \w+ Unicode + plegado de diacríticos NFKD + lower —
           las mismas reglas del tokenizer unicode61 de FTS5)
    Valida que el índice FTS5 no pierda ni desalinee tokens (con o sin acentos).
C2. MOTOR INDEPENDIENTE (solo triples ASCII originales): para triples cuyas
    palabras originales son puramente ASCII (el plegado es identidad, así que
    ambos motores comparan los mismos bytes):
        archivos(FTS5) ⊆ intersección de archivos(rg -l -i por token)
    En triples con acentos, rg (sensible a acentos) no es comparable con FTS5
    (insensible): se excluyen de C2 y quedan cubiertos por C1.

HALLAZGO DE DISEÑO (registrado en ADR-0002): rg -U con patrón ordenado
multilínea `\bw1\b[\s\S]*\bw2\b…` SUB-REPORTA coincidencias en algunos archivos
grandes (se comprobó contra SQL LIKE: FTS5 tenía razón, 5/5). Por eso rg se usa
solo en su modo robusto de token único, y la igualdad exacta se prueba contra
un tokenizador de referencia independiente.

Exit 0 solo si A, B, C1 (100%) y C2 (100%).
"""
import json
import random
import re
import sqlite3
import subprocess
import sys
import unicodedata

from corpus_config import CORPUS_DIR, DB_PATH, MANIFEST_PATH, corpus_files
from corpus_verify import coverage_report, verify_lossless

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{6,}")
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
MIN_MUESTRAS = 15


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def chunk_token_index(con: sqlite3.Connection) -> dict:
    """chunk_id -> (file_id, conjunto de tokens plegados). Barrido de referencia."""
    return {
        chunk_id: (file_id, {fold(w) for w in TOKEN_RE.findall(text)})
        for chunk_id, file_id, text in con.execute("SELECT chunk_id, file_id, text FROM chunks")
    }


def rg_files(pattern: str) -> set:
    cmd = ["rg", "-l", "-i", "--no-messages", "-e", pattern, str(CORPUS_DIR)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    return {p.rsplit("/", 1)[-1] for p in out.stdout.splitlines() if p.strip()}


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    con = sqlite3.connect(DB_PATH)

    # A. Cobertura
    cov = coverage_report(con, {p.name for p in corpus_files()}, set(manifest["files"]))
    ok_a = not (cov["faltan_en_db"] or cov["extras_en_db"] or cov["faltan_en_manifest"] or cov["extras_en_manifest"])

    # B. Reconstrucción lossless
    bad = verify_lossless(con)
    ok_b = not bad

    # C1 + C2. Diferencial semántico
    files_by_id = dict(con.execute("SELECT file_id, filename FROM docs"))
    token_idx = chunk_token_index(con)
    rows = con.execute("SELECT chunk_id, text FROM chunks").fetchall()
    rng = random.Random(42)
    candidatos = rng.sample(rows, min(60, len(rows)))
    usadas, usadas_c2, fallos_c1, fallos_c2, dispersas = 0, 0, [], [], 0
    for chunk_id, text in candidatos:
        if usadas >= 30:
            break
        vistos, raras = set(), []
        for w in WORD_RE.findall(text):
            wl = w.lower()
            if wl in vistos or not wl.isalpha():
                continue
            vistos.add(wl)
            d = len(rg_files(rf"\b{re.escape(wl)}\b"))
            if 1 <= d <= 8:
                raras.append(wl)
            if len(raras) == 3:
                break
        if len(raras) < 3:
            continue
        t = [fold(w) for w in raras]
        usadas += 1
        match = " AND ".join(f'"{w}"' for w in t)
        fts = {
            r[0]
            for r in con.execute(
                "SELECT DISTINCT filename FROM chunks_fts WHERE chunks_fts MATCH ?", (match,)
            )
        }
        brute = {
            files_by_id[file_id]
            for file_id, toks in token_idx.values()
            if set(t) <= toks
        }
        if fts != brute:
            fallos_c1.append((t, sorted(fts ^ brute)))
        if all(w.isascii() for w in raras):
            usadas_c2 += 1
            rg_inter = set.intersection(*(rg_files(rf"\b{re.escape(w)}\b") for w in t))
            faltan = fts - rg_inter
            if faltan:
                fallos_c2.append((t, sorted(faltan)))
            dispersas += len(rg_inter - fts)

    print("=== CONTROL DIFERENCIAL DEL ÍNDICE ===")
    print(f"A. Cobertura índice==disco==manifiesto: {'OK' if ok_a else 'FALLA'}")
    print(f"B. Reconstrucción lossless: {'OK (0 fallos en ' + str(manifest['file_count']) + ' archivos)' if ok_b else 'FALLA: ' + str(bad[:5])}")
    print(f"C. Diferencial semántico: {usadas} triples de tokens raros")
    if usadas:
        print(f"   C1 FTS5 == fuerza bruta (chunk): {usadas - len(fallos_c1)}/{usadas} "
              f"({100 * (usadas - len(fallos_c1)) / usadas:.0f}%)")
        if usadas_c2:
            print(f"   C2 FTS5 ⊆ rg∩ (archivo, ASCII): {usadas_c2 - len(fallos_c2)}/{usadas_c2} "
                  f"({100 * (usadas_c2 - len(fallos_c2)) / usadas_c2:.0f}%)")
        else:
            print("   C2 sin muestra ASCII; no aplica en esta corrida")
        print(f"   Dispersas (rg∩ sí, FTS5 no — informativo): {dispersas}")
        for tag, lst in (("C1", fallos_c1), ("C2", fallos_c2)):
            for t, f in lst[:5]:
                print(f"   DESACUERDO {tag} {t}: {f}")
    ok_c = (
        usadas >= MIN_MUESTRAS
        and not fallos_c1
        and (usadas_c2 == 0 or not fallos_c2)
    )
    if usadas < MIN_MUESTRAS:
        print(f"   AVISO: muestra insuficiente ({usadas} < {MIN_MUESTRAS}); C no concluyente")

    con.close()
    sys.exit(0 if (ok_a and ok_b and ok_c) else 1)


if __name__ == "__main__":
    main()
