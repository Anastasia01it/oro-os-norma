#!/usr/bin/env python3
"""Validador de fichas diligenciadas (mejora M1, ADR-0004).

Una ficha solo es aceptable si sus afirmaciones son comprobables:
  V1  meta bien formada (id, estado, norma, sello del corpus con formato valido)
  V2  el sello del corpus coincide con el manifiesto vigente
  V3  campos completados tienen REF. ARTICULO cuando el elemento lo exige
      y al menos una evidencia que las respalde (sin evidencia no hay verdad)
  V4  cada evidencia cita un campo real y trae tipo y texto citado
  V5  cada cita resuelve a lineas reales del corpus y el texto citado
      aparece verbatim en ellas (contra el indice FTS5 del paso 1)

Uso: python3 validar-ficha.py FICHA.json [--indice RUTA.sqlite] [--offline]
Exit 0 = aceptable; exit 1 = rechazada. Cero dependencias externas.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import unicodedata

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_DIR = os.path.dirname(SCRIPT_DIR)
ROOT = os.path.dirname(os.path.dirname(PKG_DIR))  # raiz del proyecto Norma
DATA_PATH = os.path.join(PKG_DIR, "data", "elementos.json")
MANIFEST_PATH = os.path.join(ROOT, "normas_procesar", "manifest.json")
DEFAULT_INDEX = os.path.join(ROOT, "sistema", "data", "corpus.index.sqlite")

ID_FICHA_RX = re.compile(r"^NP-FICHA-[A-Z]+-[0-9]+-[0-9]{4}-[0-9]+$")
NORMA_RX = re.compile(r"^[^/\\]+\.md$")
HASH_RX = re.compile(r"^[0-9a-f]{64}$")
CAMPO_RX = re.compile(r"^[A-M]\.[0-9]+[a-z]?$")
CITA_RX = re.compile(r"^([^\n]+?\.md)#L(\d+)(?:-L(\d+))?$")
ESTADOS = {"abierta", "en_progreso", "completada", "revisada", "aprobada", "archivada"}
TIPOS = {"texto", "tabla", "calculo"}


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def cargar_json(path, errores, etiqueta):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        errores.append(f"{etiqueta}: no existe {path}")
    except json.JSONDecodeError as e:
        errores.append(f"{etiqueta}: JSON invalido: {e}")
    return None


def validar(ficha_path, indice_path, offline):
    errores, advertencias = [], []
    ficha = cargar_json(ficha_path, errores, "FICHA")
    elementos_data = cargar_json(DATA_PATH, errores, "FUENTE-NP")
    if ficha is None or elementos_data is None:
        return errores, advertencias, False, None, None

    elementos = {e["id"]: e for e in elementos_data["elementos"]}

    # V1: meta
    meta = ficha.get("meta", {})
    if not ID_FICHA_RX.match(str(meta.get("id_ficha", ""))):
        errores.append(f"V1: meta.id_ficha no cumple el patron NP: {meta.get('id_ficha')!r}")
    if meta.get("estado") not in ESTADOS:
        errores.append(f"V1: meta.estado invalido: {meta.get('estado')!r}")
    if not NORMA_RX.match(str(meta.get("norma_archivo", ""))):
        errores.append(f"V1: meta.norma_archivo debe ser un .md sin rutas: {meta.get('norma_archivo')!r}")
    sello = str(meta.get("corpus_set_hash", ""))
    if not HASH_RX.match(sello):
        errores.append("V1: meta.corpus_set_hash debe ser sha256 hex de 64 caracteres")

    # V2: sello vs manifiesto
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            set_hash = json.load(f).get("set_hash", "")
        if HASH_RX.match(sello) and sello != set_hash:
            errores.append(
                f"V2: corpus_set_hash no coincide con el manifiesto vigente "
                f"(ficha: {sello[:12]}… | manifiesto: {set_hash[:12]}…). "
                f"La ficha fue producida contra otro corpus."
            )
    elif not offline:
        errores.append(f"V2: no se encontro el manifiesto del corpus en {MANIFEST_PATH}")

    # V3: cobertura de evidencia y REF. ARTICULO
    evidencia = ficha.get("evidencia")
    if not isinstance(evidencia, list) or len(evidencia) < 1:
        errores.append("V3/V4: 'evidencia' debe ser un arreglo con al menos 1 cita")
        evidencia = []
    campos_con_ev = {e.get("campo") for e in evidencia if isinstance(e, dict)}

    fases = ficha.get("fases", {})
    completados = 0
    for eid, elem in elementos.items():
        fase_canonica = str(elem["fase_lectura"])
        reg = fases.get(fase_canonica, {}).get(eid)
        if reg is None:
            for fase_declarada, contenido in fases.items():
                if isinstance(contenido, dict) and eid in contenido:
                    errores.append(
                        f"V3: {eid} esta bajo la fase {fase_declarada} pero la fuente "
                        f"lo asigna a la fase {fase_canonica}"
                    )
                    reg = contenido[eid]
                    break
        if not isinstance(reg, dict) or not reg.get("completado") or reg.get("na"):
            continue
        completados += 1
        if elem["requiere_ref_articulo"] and not str(reg.get("ref_articulo", "")).strip():
            errores.append(f"V3: {eid} completado sin REF. ARTICULO (obligatorio para este elemento)")
        if eid not in campos_con_ev:
            errores.append(f"V3: {eid} completado sin evidencia (toda afirmacion debe ser comprobable)")

    # V4: estructura de cada evidencia
    items_validos = []
    for i, ev in enumerate(evidencia):
        if not isinstance(ev, dict):
            errores.append(f"V4: evidencia[{i}] no es un objeto")
            continue
        campo = str(ev.get("campo", ""))
        cita = str(ev.get("cita", ""))
        tipo = ev.get("tipo")
        verbatim = str(ev.get("verbatim", ""))
        if not CAMPO_RX.match(campo):
            errores.append(f"V4: evidencia[{i}].campo invalido: {campo!r}")
        elif campo not in elementos:
            errores.append(f"V4: evidencia[{i}].campo no existe en la taxonomia: {campo!r}")
        if not CITA_RX.match(cita):
            errores.append(f"V4: evidencia[{i}].cita debe ser 'ARCHIVO.md#Ln' o 'ARCHIVO.md#Ln-Lm': {cita!r}")
        if tipo not in TIPOS:
            errores.append(f"V4: evidencia[{i}].tipo invalido: {tipo!r}")
        if not verbatim.strip():
            errores.append(f"V4: evidencia[{i}].verbatim vacio (se exige la cita textual)")
        if CAMPO_RX.match(campo) and CITA_RX.match(cita) and tipo in TIPOS and verbatim.strip():
            items_validos.append(ev)

    # V5: resolucion de citas contra el indice
    con = None
    if os.path.exists(indice_path):
        con = sqlite3.connect(indice_path)
    elif not offline:
        errores.append(f"V5: no se encontro el indice del corpus: {indice_path}")

    if con:
        textos = {}
        for fname, in con.execute("SELECT filename FROM docs"):
            textos[fname] = None  # carga perezosa
        for ev in items_validos:
            m = CITA_RX.match(str(ev["cita"]))
            fname, l1, l2 = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
            if fname not in textos:
                errores.append(f"V5: {ev['cita']}: el archivo no esta en el corpus")
                continue
            if textos[fname] is None:
                file_id = con.execute("SELECT file_id FROM docs WHERE filename = ?", (fname,)).fetchone()[0]
                textos[fname] = "".join(
                    t for (t,) in con.execute(
                        "SELECT text FROM chunks WHERE file_id = ? ORDER BY chunk_no", (file_id,)
                    )
                )
            lineas = textos[fname].split("\n")
            if l1 < 1 or l2 > len(lineas) or l1 > l2:
                errores.append(
                    f"V5: {ev['cita']}: rango invalido (el archivo tiene {len(lineas)} lineas)"
                )
                continue
            trozo = "\n".join(lineas[l1 - 1:l2])
            if fold(ev["verbatim"]) not in fold(trozo):
                errores.append(
                    f"V5: {ev['cita']}: el texto citado NO aparece verbatim en esas lineas"
                )
        con.close()

    if completados == 0:
        advertencias.append("La ficha no tiene ningun campo completado; validacion estructural solo.")
    return errores, advertencias, True, completados, len(items_validos)


def main():
    ap = argparse.ArgumentParser(description="Validador de fichas NP (M1: evidencia obligatoria)")
    ap.add_argument("ficha", help="Ruta del ficha.json diligenciado")
    ap.add_argument("--indice", default=DEFAULT_INDEX, help="Ruta del indice SQLite FTS5")
    ap.add_argument("--offline", action="store_true",
                    help="No exigir manifiesto/indice del corpus (solo validacion estructural)")
    args = ap.parse_args()

    errores, advertencias, ok, completados, n_ev = validar(args.ficha, args.indice, args.offline)
    print("=== VALIDACION DE FICHA ===")
    if ok:
        print(f"Campos completados: {completados} | Evidencias validas: {n_ev}")
    for a in advertencias:
        print(f"  ⚠️  {a}")
    for e in errores:
        print(f"  ❌ {e}")
    if not errores:
        print("FICHA ACEPTABLE: toda afirmacion completada es comprobable contra el corpus.")
        sys.exit(0)
    print(f"FICHA RECHAZADA: {len(errores)} problema(s). Sin evidencia no hay verdad.")
    sys.exit(1)


if __name__ == "__main__":
    main()
