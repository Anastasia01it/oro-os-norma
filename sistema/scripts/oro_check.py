#!/usr/bin/env python3
"""Verificador del set de oro (paso 4 del plan).

Principio: QUIEN MIDE DEBE SER VERDAD. Antes de usar los casos de oro para
evaluar al procesador (o a la IA), este script comprueba que cada caso de oro
es verdadero contra el corpus:
  - casos "cita":     la cita resuelve a lineas reales y el texto citado aparece
  - casos "conteo":   el patron contado sobre el archivo da exactamente el valor
  - casos "ausente":  el patron NO aparece (en el archivo, en el corpus o en
                      los nombres de archivo, segun el alcance del caso)
Un caso de oro falso es un fallo DEL SET, no de quien se evalua: se corrige el
oro o se corrige el corpus, nunca se ignora.

Uso: python3 oro_check.py [--casos sistema/oro/casos-oro.json] [--indice ...]
Exit 0 = el oro es verdadero; exit 1 = hay casos falsos o estructura invalida.
"""
import argparse
import json
import re
import sqlite3
import sys
import unicodedata

from corpus_config import DB_PATH

ID_RX = re.compile(r"^ORO-(?:[0-9]{3}|N[0-9]{2})$")
CITA_RX = re.compile(r"^([^\n]+?\.md)#L(\d+)(?:-L(\d+))?$")
VERIFICACIONES = {"cita", "conteo", "ausente"}
ALCANCES = {"archivo", "corpus", "nombres"}


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def plano(s):
    """Colapsa espacios/saltos de linea: las citas reales cruzan renglones cortados."""
    return re.sub(r"\s+", " ", s).strip()


class Corpus:
    def __init__(self, indice_path):
        self.con = sqlite3.connect(indice_path)
        self.names = [r[0] for r in self.con.execute("SELECT filename FROM docs")]
        self._texts = {}

    def text(self, fname):
        if fname not in self._texts:
            row = self.con.execute("SELECT file_id FROM docs WHERE filename = ?", (fname,)).fetchone()
            if row is None:
                return None
            self._texts[fname] = "".join(
                t for (t,) in self.con.execute(
                    "SELECT text FROM chunks WHERE file_id = ? ORDER BY chunk_no", (row[0],)
                )
            )
        return self._texts[fname]

    def all_texts(self):
        return {n: self.text(n) for n in self.names}


def verificar_caso(caso, corpus):
    """Devuelve lista de fallos (vacía = el oro es verdadero en este caso)."""
    fallos = []
    ver = caso.get("verificacion")
    esp = caso.get("esperado", {})
    fname = caso.get("norma")

    if ver == "cita":
        m = CITA_RX.match(str(esp.get("cita", "")))
        if not m:
            return [f"cita con formato invalido: {esp.get('cita')!r}"]
        cfile, l1, l2 = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
        texto = corpus.text(cfile)
        if texto is None:
            return [f"el archivo citado no esta en el corpus: {cfile}"]
        lineas = texto.split("\n")
        if l1 < 1 or l2 > len(lineas) or l1 > l2:
            return [f"rango de lineas invalido ({len(lineas)} lineas en {cfile})"]
        trozo = "\n".join(lineas[l1 - 1:l2])
        if fold(plano(esp.get("verbatim", ""))) not in fold(plano(trozo)):
            fallos.append(f"el texto citado NO aparece en {esp.get('cita')}")

    elif ver == "conteo":
        texto = corpus.text(fname)
        if texto is None:
            return [f"norma no encontrada en el corpus: {fname}"]
        try:
            rx = re.compile(esp["patron"], re.I)
        except re.error as e:
            return [f"patron de conteo invalido: {e}"]
        n = sum(1 for linea in texto.split("\n") if rx.search(fold(linea)))
        if str(n) != str(esp.get("valor")):
            fallos.append(f"conteo {n} != valor declarado {esp.get('valor')} (patron {esp['patron']!r})")

    elif ver == "ausente":
        try:
            rx = re.compile(caso["esperado"]["patron"], re.I)
        except (re.error, KeyError) as e:
            return [f"patron de ausencia invalido: {e}"]
        alcance = caso.get("alcance")
        if alcance == "archivo":
            texto = corpus.text(fname)
            if texto is None:
                return [f"norma no encontrada en el corpus: {fname}"]
            coincidencias = [i + 1 for i, l in enumerate(texto.split("\n")) if rx.search(fold(l))]
        elif alcance == "corpus":
            coincidencias = [
                f"{n}:L{i+1}" for n, t in corpus.all_texts().items()
                for i, l in enumerate(t.split("\n")) if rx.search(fold(l))
            ][:5]
        elif alcance == "nombres":
            coincidencias = [n for n in corpus.names if rx.search(fold(n))]
        else:
            return [f"alcance invalido: {alcance!r}"]
        if coincidencias:
            fallos.append(f"el patron SI aparece (el caso negativo es falso): {coincidencias[:5]}")

    return fallos


def estructura(casos):
    fallos = []
    vistos = set()
    for c in casos:
        cid = c.get("id", "")
        if not ID_RX.match(cid):
            fallos.append(f"id invalido: {cid!r}")
        if cid in vistos:
            fallos.append(f"id duplicado: {cid}")
        vistos.add(cid)
        if not str(c.get("pregunta", "")).strip():
            fallos.append(f"{cid}: pregunta vacia")
        ver = c.get("verificacion")
        if ver not in VERIFICACIONES:
            fallos.append(f"{cid}: verificacion invalida: {ver!r}")
        if c.get("alcance") not in ALCANCES:
            fallos.append(f"{cid}: alcance invalido: {c.get('alcance')!r}")
        esp = c.get("esperado")
        if not isinstance(esp, dict):
            fallos.append(f"{cid}: esperado debe ser objeto")
            continue
        if ver == "cita" and not (esp.get("cita") and esp.get("verbatim")):
            fallos.append(f"{cid}: caso 'cita' requiere esperado.cita y esperado.verbatim")
        if ver == "conteo" and not (esp.get("patron") and esp.get("valor") is not None):
            fallos.append(f"{cid}: caso 'conteo' requiere esperado.patron y esperado.valor")
        if ver == "ausente" and not esp.get("patron"):
            fallos.append(f"{cid}: caso 'ausente' requiere esperado.patron")
        if c.get("alcance") == "archivo" and not c.get("norma"):
            fallos.append(f"{cid}: alcance 'archivo' requiere norma")
    return fallos


def main():
    ap = argparse.ArgumentParser(description="Verificador del set de oro")
    ap.add_argument("--casos", default=None, help="Ruta de casos-oro.json")
    ap.add_argument("--indice", default=str(DB_PATH), help="Ruta del indice SQLite")
    args = ap.parse_args()

    casos_path = args.casos or str(DB_PATH.parents[1] / "oro" / "casos-oro.json")
    with open(casos_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    casos = data["casos"]

    print("=== VERIFICACION DEL SET DE ORO ===")
    print(f"Casos: {len(casos)} | indice: {args.indice}")

    corpus = Corpus(args.indice)
    fallos_total = 0

    e = estructura(casos)
    for x in e:
        print(f"  ❌ ESTRUCTURA: {x}")
    fallos_total += len(e)

    ok = 0
    for caso in casos:
        fallos = verificar_caso(caso, corpus)
        if fallos:
            fallos_total += len(fallos)
            for x in fallos:
                print(f"  ❌ {caso.get('id')}: {x}")
        else:
            ok += 1

    print(f"\nOro verdadero: {ok}/{len(casos)} casos")
    if fallos_total == 0:
        print("SET DE ORO APROBADO: la regla de medir es verdad.")
        sys.exit(0)
    print(f"SET DE ORO RECHAZADO: {fallos_total} problema(s). Corregir el oro o el corpus.")
    sys.exit(1)


if __name__ == "__main__":
    main()
