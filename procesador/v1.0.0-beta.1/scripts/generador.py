#!/usr/bin/env python3
"""
generador.py — Motor de derivacion del sistema Normativa-Procesador (NP)
Version: 1.0.0-alpha.3
Patron: Single Source of Truth (SSOT) + Generacion Derivada

Uso:
    python scripts/generador.py --all
    python scripts/generador.py --validate
    python scripts/generador.py --dry-run --all
    python scripts/generador.py --check-narrativos
    python scripts/generador.py --categorias
    python scripts/generador.py --schema
    python scripts/generador.py --sql
    python scripts/generador.py --ficha
    python scripts/generador.py --matriz
    python scripts/generador.py --glosario
"""

import json
import os
import sys
import argparse
import re
import hashlib
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "elementos.json")
SCHEMA_PATH = os.path.join(BASE_DIR, "data", "schema-elementos.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

NARRATIVOS = [
    os.path.join(BASE_DIR, "docs", "estrategia", "ESTRATEGIA.md"),
    os.path.join(BASE_DIR, "docs", "handoff", "HANDOFF.md"),
    os.path.join(BASE_DIR, "BACKLOG.md"),
    os.path.join(BASE_DIR, "README.md"),
]

def cargar_elementos():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def cargar_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def now_iso():
    return datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%dT%H:%M:%S%z")

def stamp_fuente(data):
    """Marca de generación de artefactos: la fecha de la FUENTE (meta.fecha).

    Determinista (mejora M3, ADR-0003): regenerar con la misma fuente produce
    artefactos byte-por-byte idénticos, y la marca amarra cada artefacto a la
    versión exacta de su fuente — coherente con el principio P7 (SSOT).
    El reloj de pared (now_iso) queda solo para metadatos operativos, no para
    contenido derivado.
    """
    return data["meta"]["fecha"]

def hash_deterministic(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]

def get_stats(elementos):
    cats = sorted(set(e["categoria"] for e in elementos))
    fases = sorted(set(e["fase_lectura"] for e in elementos))
    return {
        "total_elementos": len(elementos),
        "categorias": len(cats),
        "fases_lectura": len(fases),
        "categorias_lista": cats,
        "fases_lista": fases,
        "por_categoria": {cat: len([e for e in elementos if e["categoria"] == cat]) for cat in cats},
        "por_fase": {str(f): len([e for e in elementos if e["fase_lectura"] == f]) for f in fases},
    }

# ================================================================
# VALIDACION SSOT
# ================================================================
def validar_ssot(data, verbose=True):
    elementos = data["elementos"]
    errores = []
    warnings = []
    all_ids = set(e["id"] for e in elementos)

    ids = [e["id"] for e in elementos]
    dupes = {id for id in ids if ids.count(id) > 1}
    if dupes:
        errores.append(f"[E001] IDs duplicados: {sorted(dupes)}")

    campos_req = ["id", "categoria", "nombre", "descripcion", "fase_lectura", "estado", "origen", "tipo_campo", "requiere_ref_articulo", "dependencias", "glosario_terminos"]
    for e in elementos:
        for campo in campos_req:
            if campo not in e:
                errores.append(f"[E002] {e['id']}: falta campo obligatorio '{campo}'")

    for e in elementos:
        for dep in e.get("dependencias", []):
            if dep not in all_ids:
                errores.append(f"[E003] {e['id']}: dependencia rota -> '{dep}' no existe")

    cats_validas = set("ABCDEFGHIJKLM")
    for e in elementos:
        if e["categoria"] not in cats_validas:
            errores.append(f"[E004] {e['id']}: categoria invalida '{e['categoria']}'")

    for e in elementos:
        if not (0 <= e["fase_lectura"] <= 9):
            errores.append(f"[E005] {e['id']}: fase invalida {e['fase_lectura']}")

    estados_validos = {"validado", "pendiente", "borrador", "deprecado"}
    for e in elementos:
        if e["estado"] not in estados_validos:
            errores.append(f"[E006] {e['id']}: estado invalido '{e['estado']}'")

    origenes_validos = {"base", "CRA", "SSPD", "campo", "usuario"}
    for e in elementos:
        if e["origen"] not in origenes_validos:
            errores.append(f"[E007] {e['id']}: origen invalido '{e['origen']}'")

    tipos_validos = {"checkbox", "texto", "numero", "fecha", "lista", "formula", "tabla"}
    for e in elementos:
        if e["tipo_campo"] not in tipos_validos:
            errores.append(f"[E008] {e['id']}: tipo_campo invalido '{e['tipo_campo']}'")

    id_pattern = re.compile(r"^[A-Z]\.\d+[a-z]?$")
    for e in elementos:
        if not id_pattern.match(e["id"]):
            errores.append(f"[E009] {e['id']}: formato de ID invalido")

    for e in elementos:
        if not e["descripcion"].strip():
            warnings.append(f"[W001] {e['id']}: descripcion vacia")
        if not e["nombre"].strip():
            errores.append(f"[E010] {e['id']}: nombre vacio")

    campos_derivados = ["total_elementos", "categorias", "fases_lectura"]
    for campo in campos_derivados:
        if campo in data.get("meta", {}):
            warnings.append(f"[W002] meta.{campo} es atributo derivado. Eliminar. Computar dinamicamente.")

    if "version" not in data.get("meta", {}):
        errores.append("[E011] meta.version obligatorio")
    if "fecha" not in data.get("meta", {}):
        errores.append("[E012] meta.fecha obligatorio")

    # E013: Coherencia de fase padre-hijo
    # Elementos con sufijo de letra (ej. F.35a) deben compartir fase con su padre (F.35)
    id_to_element = {e["id"]: e for e in elementos}
    for e in elementos:
        eid = e["id"]
        # Detectar IDs con sufijo de letra: patron X.YZa donde Z es numero y a es letra
        match = re.match(r'^([A-Z]\.\d+)[a-z]$', eid)
        if match:
            parent_id = match.group(1)
            if parent_id in id_to_element:
                parent = id_to_element[parent_id]
                if e["fase_lectura"] != parent["fase_lectura"]:
                    errores.append(
                        f"[E013] {eid}: fase {e['fase_lectura']} no coincide con padre "
                        f"{parent_id} (fase {parent['fase_lectura']}). "
                        f"Los sub-elementos deben compartir fase con su elemento padre."
                    )

    if verbose:
        stats = get_stats(elementos)
        print(f"=== VALIDACION SSOT ===")
        print(f"Elementos: {stats['total_elementos']}")
        print(f"Categorias: {stats['categorias']} ({', '.join(stats['categorias_lista'])})")
        print(f"Fases: {stats['fases_lectura']} ({', '.join(map(str, stats['fases_lista']))})")
        print(f"Errores: {len(errores)}")
        print(f"Warnings: {len(warnings)}")
        for e in errores:
            print(f"  ❌ {e}")
        for w in warnings:
            print(f"  ⚠️  {w}")
        print("")

    return len(errores) == 0, errores, warnings

# ================================================================
# CHECK NARRATIVOS
# ================================================================
def check_narrativos(data, verbose=True):
    elementos = data["elementos"]
    all_ids = set(e["id"] for e in elementos)
    stats = get_stats(elementos)
    issues = []
    refs_totales = 0

    for path in NARRATIVOS:
        if not os.path.exists(path):
            issues.append(f"[N001] Archivo no encontrado: {path}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        refs = set(re.findall(r"[A-Z]\.\d+[a-z]?", content))
        refs_totales += len(refs)
        rotas = refs - all_ids
        if rotas:
            issues.append(f"[N002] {os.path.basename(path)}: {len(rotas)} refs rotas: {sorted(rotas)}")

    # N003: conteos numericos vs stats computados (mejora M2, cierra hallazgo F-2).
    # Solo se verifican DECLARACIONES DE TOTAL DEL SISTIMA (no conteos por
    # categoria, ni entradas de historial/changelog, que son registros legitimos
    # del pasado). Un total declarado distinto al computado = documento atrasado.
    esperados = {
        "elementos": stats["total_elementos"],
        "categorias": stats["categorias"],
        "fases": stats["fases_lectura"],
    }
    HISTORIA_RX = re.compile(r"^\s*(?:\d{4}-\d{2}-\d{2}|\|\s*\d+\s*\||v?\d+\.\d+\.\d+)", re.I)
    PATRONES_STATS = [
        ("elementos", re.compile(r"\btotal\s+(?:de\s+)?elementos\s*[:=|]\s*(\d{1,4})\b", re.I)),
        ("elementos", re.compile(r"\belementos\s+totales\s*[:=|]\s*(\d{1,4})\b", re.I)),
        ("elementos", re.compile(r"^\s*\|?\s*elementos\s*\|\s*(\d{1,4})\b", re.I | re.M)),
        ("categorias", re.compile(r"^\s*\|?\s*categorias\s*\|\s*(\d{1,4})\b", re.I | re.M)),
        ("fases", re.compile(r"\b(\d{1,4})\s+fases\b", re.I)),
        ("fases", re.compile(r"\bfases(?:\s+de\s+lectura)?\s*[:=|]\s*(\d{1,4})\b", re.I)),
    ]
    for path in NARRATIVOS:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if HISTORIA_RX.match(line):
                    continue
                for key, rx in PATRONES_STATS:
                    for m in rx.finditer(line):
                        declarado = int(m.group(1))
                        if declarado != esperados[key]:
                            issues.append(
                                f"[N003] {os.path.basename(path)}: declara '{key} = {declarado}' "
                                f"pero la fuente computa {esperados[key]}"
                            )

    if verbose:
        print(f"=== CHECK NARRATIVOS ===")
        print(f"Archivos: {len([p for p in NARRATIVOS if os.path.exists(p)])}")
        print(f"Refs totales: {refs_totales}")
        print(f"Issues: {len(issues)}")
        for issue in issues:
            print(f"  ⚠️  {issue}")
        print("")

    return len(issues) == 0, issues

# ================================================================
# DRY RUN
# ================================================================
class DryRunWriter:
    def __init__(self):
        self.files = {}
        self.modified = 0
        self.new = 0
        self.unchanged = 0

    def write(self, path, content):
        rel = os.path.relpath(path, BASE_DIR)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                old = f.read()
            if old == content:
                self.unchanged += 1
                self.files[rel] = "UNCHANGED"
            else:
                self.modified += 1
                old_lines = old.splitlines()
                new_lines = content.splitlines()
                changed = sum(1 for a, b in zip(old_lines, new_lines) if a != b)
                changed += abs(len(old_lines) - len(new_lines))
                self.files[rel] = f"MODIFIED ({changed} lineas)"
        else:
            self.new += 1
            self.files[rel] = f"NEW ({content.count(chr(10))} lineas)"

    def report(self):
        print(f"=== DRY RUN ===")
        print(f"Nuevos: {self.new} | Modificados: {self.modified} | Sin cambios: {self.unchanged}")
        for rel, status in sorted(self.files.items()):
            icon = "🆕" if "NEW" in status else "📝" if "MODIFIED" in status else "✅"
            print(f"  {icon} {rel}: {status}")
        print("")

def get_writer(dry_run=False):
    return DryRunWriter() if dry_run else None

def write_file(writer, path, content):
    if writer:
        writer.write(path, content)
    else:
        ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


# ================================================================
# GENERADOR 1: CATEGORIAS .md
# ================================================================
def generar_categorias(data, writer=None):
    out_dir = os.path.join(OUTPUT_DIR, "categorias")
    elementos = data["elementos"]
    stats = get_stats(elementos)
    cats = {}
    for e in elementos:
        c = e["categoria"]
        if c not in cats:
            cats[c] = []
        cats[c].append(e)

    nombres_cat = {
        "A": "METADATOS DE IDENTIFICACION",
        "B": "ESTRUCTURA FORMAL INTERNA",
        "C": "ESTADOS DE VIGENCIA",
        "D": "RELACIONES NORMATIVAS",
        "E": "CONTROL DE VERSIONES",
        "F": "ANALISIS OPERATIVO",
        "G": "METADATOS DEL ANALISIS",
        "H": "ELEMENTOS ESPECIALES",
        "I": "JERARQUIA Y VALIDEZ FORMAL",
        "J": "INTERPRETACION Y APLICACION",
        "K": "EFICACIA Y APLICABILIDAD",
        "L": "ANALISIS ECONOMICO / AIR",
        "M": "MECANISMOS DE GOBERNANZA Y SEGUIMIENTO",
    }

    for cat, elems in sorted(cats.items()):
        fname = f"{cat}-{nombres_cat[cat].replace(' ', '-').replace('/', '-')}.md"
        fpath = os.path.join(out_dir, fname)
        lines = [
            f"# CATEGORIA {cat} — {nombres_cat[cat]}",
            f"# NP-CAT-{cat}  v{data['meta']['version']}  {stamp_fuente(data)}",
            "",
            "================================================================================",
            "1.  DEFINICION",
            "================================================================================",
            "",
            f"[Auto-generado desde data/elementos.json — {len(elems)} elementos]",
            "",
            "================================================================================",
            "2.  ELEMENTOS",
            "================================================================================",
            "",
            "#     Elemento                              Descripcion",
            "----- ------------------------------------- -----------------------------------",
        ]
        for e in elems:
            origen_tag = f" [{e['origen'].upper()}]" if e['origen'] != 'base' else ""
            desc = e['descripcion'].replace("\n", " ")
            lines.append(f"{e['id']:<5} {e['nombre']:<37} {desc}{origen_tag}")
        lines.extend([
            "",
            "================================================================================",
            "3.  METADATOS",
            "================================================================================",
            "",
            f"| Campo          | Valor |",
            f"|----------------|-------|",
            f"| Categoria      | {cat} |",
            f"| Elementos      | {len(elems)} |",
            f"| Fase principal | {elems[0]['fase_lectura']} |",
            f"| Origenes       | {', '.join(sorted(set(e['origen'] for e in elems)))} |",
            f"| Hash fuente    | {hash_deterministic(elems)} |",
            "",
        ])
        write_file(writer, fpath, "\n".join(lines))
        if not writer:
            print(f"  [OK] {fname} ({len(elems)} elementos)")

# ================================================================
# GENERADOR 2: SCHEMA JSON
# ================================================================
def generar_schema(data, writer=None):
    out_path = os.path.join(OUTPUT_DIR, "schema-norma.json")
    elementos = data["elementos"]
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Ficha Normativa NP",
        "description": "Esquema de datos para el sistema Normativa-Procesador",
        "version": data["meta"]["version"],
        "hash_fuente": hash_deterministic(elementos),
        "type": "object",
        "required": ["meta", "fases", "evidencia"],
        "properties": {
            "meta": {
                "type": "object",
                "properties": {
                    "id_ficha": {"type": "string", "pattern": "^NP-FICHA-[A-Z]+-[0-9]+-[0-9]{4}-[0-9]+$"},
                    "version": {"type": "string"},
                    "fecha_analisis": {"type": "string", "format": "date-time"},
                    "analista": {"type": "string"},
                    "organizacion": {"type": "string"},
                    "proposito": {"type": "string"},
                    "estado": {"type": "string", "enum": ["abierta", "en_progreso", "completada", "revisada", "aprobada", "archivada"]},
                    "norma_archivo": {"type": "string", "pattern": "^[^/\\\\]+\\.md$"},
                    "corpus_set_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
                }
            },
            "evidencia": {
                "type": "array",
                "minItems": 1,
                "description": "Cita verificable por cada campo completado (M1)",
                "items": {
                    "type": "object",
                    "required": ["campo", "cita", "tipo", "verbatim"],
                    "properties": {
                        "campo": {"type": "string", "pattern": "^[A-M]\\.[0-9]+[a-z]?$"},
                        "cita": {"type": "string", "pattern": "^[^\\n]+\\.md#L[0-9]+(-L[0-9]+)?$"},
                        "tipo": {"type": "string", "enum": ["texto", "tabla", "calculo"]},
                        "verbatim": {"type": "string", "minLength": 1}
                    }
                }
            },
            "fases": {"type": "object"}
        }
    }
    fases = {str(i): {"type": "object", "properties": {}} for i in range(10)}
    for e in elementos:
        fase = str(e["fase_lectura"])
        prop = {
            "type": "object",
            "properties": {
                "completado": {"type": "boolean"},
                "na": {"type": "boolean"},
                "valor": {"type": "string"},
                "ref_articulo": {"type": "string"},
                "notas": {"type": "string"}
            }
        }
        if e["requiere_ref_articulo"]:
            prop["properties"]["ref_articulo"]["minLength"] = 1
        fases[fase]["properties"][e["id"]] = prop
    schema["properties"]["fases"]["properties"] = fases
    write_file(writer, out_path, json.dumps(schema, ensure_ascii=False, indent=2))
    if not writer:
        print(f"  [OK] schema-norma.json ({len(elementos)} definiciones)")

# ================================================================
# GENERADOR 3: MODELO RELACIONAL SQL
# ================================================================
def generar_sql(data, writer=None):
    out_path = os.path.join(OUTPUT_DIR, "modelo-relacional.sql")
    elementos = data["elementos"]
    stats = get_stats(elementos)
    cats = stats["categorias_lista"]

    lines = [
        "-- MODELO RELACIONAL — Normativa-Procesador",
        f"-- Version: {data['meta']['version']}",
        f"-- Hash fuente: {hash_deterministic(elementos)}",
        f"-- Generado: {stamp_fuente(data)}",
        "-- Fuente: data/elementos.json",
        "",
        "-- ================================================================",
        "-- TABLAS PRINCIPALES",
        "-- ================================================================",
        "",
        "CREATE TABLE IF NOT EXISTS normas (",
        "    id SERIAL PRIMARY KEY,",
        "    urn VARCHAR(255) UNIQUE,",
        "    tipo VARCHAR(50),",
        "    numero VARCHAR(50),",
        "    titulo TEXT,",
        "    autoridad_emisora VARCHAR(255),",
        "    fecha_expedicion DATE,",
        "    fecha_publicacion DATE,",
        "    fecha_vigencia DATE,",
        "    estado VARCHAR(50),",
        "    texto_original TEXT,",
        "    texto_consolidado TEXT,",
        "    created_at TIMESTAMP DEFAULT NOW()",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS fichas (",
        "    id SERIAL PRIMARY KEY,",
        "    id_ficha VARCHAR(100) UNIQUE NOT NULL,",
        "    norma_id INTEGER REFERENCES normas(id),",
        "    analista VARCHAR(255),",
        "    organizacion VARCHAR(255),",
        "    proposito TEXT,",
        "    estado VARCHAR(50),",
        "    fecha_analisis TIMESTAMP,",
        "    puntuacion_calidad INTEGER CHECK (puntuacion_calidad BETWEEN 0 AND 50),",
        "    created_at TIMESTAMP DEFAULT NOW()",
        ");",
        "",
    ]
    for cat in cats:
        cat_elems = [e for e in elementos if e["categoria"] == cat]
        lines.extend([
            f"CREATE TABLE IF NOT EXISTS valores_cat_{cat} (",
            "    id SERIAL PRIMARY KEY,",
            "    ficha_id INTEGER REFERENCES fichas(id) ON DELETE CASCADE,",
        ])
        for e in cat_elems:
            safe_id = e["id"].replace(".", "_")
            lines.append(f"    {safe_id}_completado BOOLEAN DEFAULT FALSE,")
            lines.append(f"    {safe_id}_na BOOLEAN DEFAULT FALSE,")
            lines.append(f"    {safe_id}_valor TEXT,")
            lines.append(f"    {safe_id}_ref_articulo VARCHAR(100),")
            lines.append(f"    {safe_id}_notas TEXT,")
        lines.extend([
            "    UNIQUE(ficha_id)",
            ");",
            "",
        ])
    lines.extend([
        "-- ================================================================",
        "-- INDICES",
        "-- ================================================================",
        "",
        "CREATE INDEX idx_normas_tipo ON normas(tipo);",
        "CREATE INDEX idx_normas_autoridad ON normas(autoridad_emisora);",
        "CREATE INDEX idx_normas_fecha ON normas(fecha_vigencia);",
        "CREATE INDEX idx_fichas_norma ON fichas(norma_id);",
        "CREATE INDEX idx_fichas_estado ON fichas(estado);",
        "",
        "-- ================================================================",
        "-- DATOS DE CATEGORIAS (maestra)",
        "-- ================================================================",
        "",
        "CREATE TABLE IF NOT EXISTS categorias (",
        "    codigo CHAR(1) PRIMARY KEY,",
        "    nombre VARCHAR(100) NOT NULL,",
        "    total_elementos INTEGER",
        ");",
        "",
    ])
    nombres = {
        "A": "METADATOS DE IDENTIFICACION", "B": "ESTRUCTURA FORMAL INTERNA",
        "C": "ESTADOS DE VIGENCIA", "D": "RELACIONES NORMATIVAS",
        "E": "CONTROL DE VERSIONES", "F": "ANALISIS OPERATIVO",
        "G": "METADATOS DEL ANALISIS", "H": "ELEMENTOS ESPECIALES",
        "I": "JERARQUIA Y VALIDEZ FORMAL", "J": "INTERPRETACION Y APLICACION",
        "K": "EFICACIA Y APLICABILIDAD", "L": "ANALISIS ECONOMICO / AIR",
        "M": "MECANISMOS DE GOBERNANZA Y SEGUIMIENTO",
    }
    for cat in cats:
        n = stats["por_categoria"][cat]
        lines.append(f"INSERT INTO categorias (codigo, nombre, total_elementos) VALUES ('{cat}', '{nombres[cat]}', {n}) ON CONFLICT (codigo) DO UPDATE SET total_elementos = EXCLUDED.total_elementos;")
    lines.append("")
    write_file(writer, out_path, "\n".join(lines))
    if not writer:
        print(f"  [OK] modelo-relacional.sql ({len(cats)} tablas + 4 base)")


# ================================================================
# GENERADOR 4: FICHA-NORMA.md
# ================================================================
def generar_ficha(data, writer=None):
    out_path = os.path.join(OUTPUT_DIR, "ficha-norma.md")
    elementos = data["elementos"]
    stats = get_stats(elementos)

    lines = [
        "# FICHA DE LECTURA MANUAL DE NORMAS",
        f"# NP-FICHA  v{data['meta']['version']}  {stamp_fuente(data)}",
        f"# Hash fuente: {hash_deterministic(elementos)}",
        "",
        "================================================================================",
        "INSTRUCCIONES DE USO",
        "================================================================================",
        "",
        "1. Complete cada campo marcando [x] o dejando [ ] segun aplique.",
        "2. Use el campo VALOR para registrar el dato extraido.",
        "3. Use REF. ARTICULO para citar la disposicion que sustenta el dato.",
        "4. Use NOTAS para registrar observaciones, dudas o advertencias.",
        "5. Al finalizar cada fase, tome la decision de continuidad.",
        "6. EVIDENCIA OBLIGATORIA (M1): todo campo marcado completado debe tener",
        "   al menos una cita en el bloque de evidencia de ficha.json (archivo del",
        "   corpus + numero(s) de linea + cita textual exacta). Sin evidencia no",
        "   hay verdad: el validador rechaza lo que no se pueda comprobar.",
        "7. ficha.json debe registrar norma_archivo (el .md analizado) y",
        "   corpus_set_hash (sello del corpus, en normas_procesar/manifest.json).",
        "8. Valide siempre con: python3 scripts/validar-ficha.py ficha.json",
        "",
        f"**Total de campos:** {stats['total_elementos']}",
        f"**Categorias:** {stats['categorias']} ({', '.join(stats['categorias_lista'])})",
        f"**Fases:** {stats['fases_lectura']} ({', '.join(map(str, stats['fases_lista']))})",
        "",
    ]
    fases = {str(i): [] for i in range(10)}
    for e in elementos:
        fases[str(e["fase_lectura"])].append(e)
    nombres_fase = {
        "0": "PREPARACION", "1": "IDENTIFICACION FORMAL", "2": "VIGENCIA Y EFICACIA",
        "3": "VERSIONES", "4": "RELACIONES NORMATIVAS", "5": "ANALISIS OPERATIVO",
        "6": "INTERPRETACION", "7": "ELEMENTOS ESPECIALES", "8": "ANALISIS ECONOMICO / AIR",
        "9": "CIERRE Y METADATOS",
    }
    for fase_num in range(10):
        fase_str = str(fase_num)
        elems = fases.get(fase_str, [])
        if not elems:
            continue
        lines.extend([
            "",
            "================================================================================",
            f"FASE {fase_num} — {nombres_fase[fase_str]}",
            "================================================================================",
            "",
        ])
        cats_in_fase = {}
        for e in elems:
            c = e["categoria"]
            if c not in cats_in_fase:
                cats_in_fase[c] = []
            cats_in_fase[c].append(e)
        for cat in sorted(cats_in_fase.keys()):
            cat_elems = cats_in_fase[cat]
            lines.append(f"### Categoria {cat} ({len(cat_elems)} elementos)")
            lines.append("")
            for e in cat_elems:
                lines.append(f"- [ ] **{e['id']}** — {e['nombre']}")
                lines.append(f"  - VALOR: _______________")
                if e["requiere_ref_articulo"]:
                    lines.append(f"  - REF. ARTICULO: _______________ (obligatorio)")
                else:
                    lines.append(f"  - REF. ARTICULO: _______________")
                lines.append(f"  - NOTAS: _______________")
                lines.append("")
        lines.extend([
            "---",
            f"**Decision Fase {fase_num}:** [ ] CONTINUAR  [ ] PAUSAR  [ ] ABANDONAR",
            f"**Firma:** _______________  **Fecha:** _______________",
            "",
        ])
    lines.extend([
        "",
        "================================================================================",
        "RESUMEN EJECUTIVO",
        "================================================================================",
        "",
        "1. Norma analizada: _________________________________________________",
        "2. Tipo y numero: _________________________________________________",
        "3. Estado de vigencia: _________________________________________________",
        f"4. Elementos completados: _____ / {stats['total_elementos']}",
        "5. Elementos N/A: _____",
        "6. Conflictos detectados: _____",
        "7. Recomendaciones: _________________________________________________",
        "8. Nivel de certeza: [ ] Alta  [ ] Media  [ ] Baja",
        "",
        "================================================================================",
        "CHECKLIST DE CALIDAD DEL ANALISIS (max. 50 puntos)",
        "================================================================================",
        "",
        "- [ ] Todos los metadatos de identificacion completos (A) ........... 5 pts",
        "- [ ] Estructura formal mapeada (B) ................................. 5 pts",
        "- [ ] Estado de vigencia verificado (C) ............................. 5 pts",
        "- [ ] Relaciones normativas trazadas (D) ............................ 5 pts",
        "- [ ] Versiones documentadas (E) .................................... 5 pts",
        "- [ ] Analisis operativo completo (F+M) ............................. 10 pts",
        "- [ ] Interpretacion aplicada (J) ................................... 5 pts",
        "- [ ] Metadatos del analisis registrados (G) ........................ 5 pts",
        "- [ ] Elementos especiales identificados (H) ........................ 5 pts",
        "",
        "**PUNTUACION TOTAL: _____ / 50**",
        "",
        "================================================================================",
        "CIERRE DE LA FICHA",
        "================================================================================",
        "",
        "Analista: _____________________________  Firma: _____________________________",
        "Revisor: _____________________________  Firma: _____________________________",
        "Fecha de cierre: _____________________________",
        "Archivo: _____________________________",
        "",
        "================================================================================",
        "BLOQUE DE EVIDENCIA (ficha.json — obligatorio, ver M1)",
        "================================================================================",
        "",
        "La ficha diligenciada debe acompañarse de un ficha.json validable contra",
        "output/schema-norma.json. Formato minimo del bloque de evidencia:",
        "",
        '{',
        '  "meta": {',
        '    "id_ficha": "NP-FICHA-LEY-142-1994-001",',
        '    "norma_archivo": "LEY-142-1994.md",',
        '    "corpus_set_hash": "<sello de normas_procesar/manifest.json>",',
        '    "estado": "completada",',
        '    ...',
        '  },',
        '  "fases": { "0": { "A.1": { "completado": true, "valor": "...",',
        '    "ref_articulo": "Art. 1", "notas": "" }, ... }, ... },',
        '  "evidencia": [',
        '    {',
        '      "campo": "A.1",',
        '      "cita": "LEY-142-1994.md#L10-L12",',
        '      "tipo": "texto",',
        '      "verbatim": "texto exacto copiado de esas lineas"',
        '    }',
        '  ]',
        '}',
        "",
        "Reglas: (a) todo campo con completado=true debe tener >= 1 evidencia;",
        "(b) la cita debe resolver a lineas reales del corpus (verificable con",
        "validar-ficha.py contra el indice FTS5); (c) el texto citado debe",
        "aparecer verbatim en las lineas indicadas; (d) corpus_set_hash debe",
        "coincidir con el manifiesto del corpus analizado.",
        "",
    ])
    write_file(writer, out_path, "\n".join(lines))
    if not writer:
        print(f"  [OK] ficha-norma.md ({stats['total_elementos']} campos)")

# ================================================================
# GENERADOR 5: MATRIZ DE INTERDEPENDENCIA
# ================================================================
def generar_matriz(data, writer=None):
    out_path = os.path.join(OUTPUT_DIR, "matriz-interdependencia.md")
    elementos = data["elementos"]
    stats = get_stats(elementos)
    all_ids = set(e["id"] for e in elementos)

    # Solo incluir reglas cuyos IDs existen en la fuente
    reglas_raw = [
        ("C.3", "Derogada total", ["D.2", "E.5", "F.23"], "Si una norma se deroga totalmente, se activan relaciones de derogacion, versiones derogadas y vacios normativos."),
        ("C.12", "Interpretacion autorizada", ["J.8", "G.7"], "Si hay interpretacion autorizada, se activa interpretacion conforme y conflictos de interpretacion."),
        ("F.30", "Formula detectada", ["F.31", "F.32", "F.33", "F.34"], "Si hay formula, deben verificarse variables, procedimiento, casos limite y tablas."),
        ("F.35", "Indicador detectado", ["F.35a", "F.35b", "F.35c"], "Si hay indicador, verificar metas escalonadas, compuestos y consecuencias."),
        ("F.36", "Metodologia detectada", ["F.36a", "F.36b", "F.36c"], "Si hay metodologia, verificar principios, validacion y aprobacion."),
        ("A.30", "Caracter particular", ["A.31", "M.7"], "Si la norma es de caracter particular, verificar publicidad y recursos especificos."),
    ]

    reglas = []
    for origen, evento, destinos, razon in reglas_raw:
        if origen not in all_ids:
            continue
        destinos_validos = [d for d in destinos if d in all_ids]
        if destinos_validos:
            reglas.append((origen, evento, destinos_validos, razon))

    lines = [
        "# MATRIZ DE INTERDEPENDENCIA",
        f"# NP-MATRIZ  v{data['meta']['version']}  {stamp_fuente(data)}",
        f"# Hash fuente: {hash_deterministic(elementos)}",
        "",
        "================================================================================",
        "1.  REGLAS DE PROPAGACION OBLIGATORIAS",
        "================================================================================",
        "",
        "| Elemento origen | Evento | Elementos destino | Razon |",
        "|-----------------|--------|-------------------|-------|",
    ]
    for origen, evento, destinos, razon in reglas:
        dest_str = ", ".join(destinos)
        lines.append(f"| {origen} | {evento} | {dest_str} | {razon} |")
    lines.extend([
        "",
        "================================================================================",
        "2.  MAPA DE IMPACTO POR CATEGORIA",
        "================================================================================",
        "",
    ])
    cats = stats["categorias_lista"]
    lines.append("| Origen \\ Destino | " + " | ".join(cats) + " |")
    lines.append("|" + "-" * 8 + "|" + "|".join("-" * 3 for _ in cats) + "|")
    for c1 in cats:
        row = [f"**{c1}**"]
        for c2 in cats:
            if c1 == c2:
                row.append("—")
            else:
                count = sum(1 for e in elementos if e["categoria"] == c1 and c2 in e.get("dependencias", []))
                row.append(str(count) if count > 0 else "·")
        lines.append("| " + " | ".join(row) + " |")
    lines.extend([
        "",
        "================================================================================",
        "3.  INDICE DE SENSIBILIDAD POR CATEGORIA",
        "================================================================================",
        "",
        "| Categoria | Elementos | Conexiones salientes | Score de sensibilidad |",
        "|-----------|-----------|----------------------|----------------------|",
    ])
    for cat in cats:
        n = stats["por_categoria"][cat]
        conex = sum(len(e.get("dependencias", [])) for e in elementos if e["categoria"] == cat)
        score = min(5, max(1, conex // 3 + 1))
        lines.append(f"| {cat} | {n} | {conex} | {'★' * score}{'☆' * (5-score)} |")
    lines.append("")
    write_file(writer, out_path, "\n".join(lines))
    if not writer:
        print(f"  [OK] matriz-interdependencia.md ({len(reglas)} reglas validas)")

# ================================================================
# GENERADOR 6: GLOSARIO DERIVADO
# ================================================================
def generar_glosario(data, writer=None):
    out_path = os.path.join(OUTPUT_DIR, "glosario-derivado.md")
    elementos = data["elementos"]
    all_ids = set(e["id"] for e in elementos)

    terminos = {}
    for e in elementos:
        for term in e.get("glosario_terminos", []):
            if term not in terminos:
                terminos[term] = []
            terminos[term].append(e["id"])

    terminos_implicitos = {
        "vacatio legis": ["A.10", "C.15"],
        "erga omnes": ["A.30"],
        "inter partes": ["A.30"],
        "interpretacion conforme": ["C.18", "J.8"],
        "eficacia ultraactiva": ["C.20", "K.5"],
        "control de constitucionalidad": ["I.5", "I.6", "H.11"],
        "debido proceso": ["M.2"],
        "regulacion asimetrica": ["F.62"],
        "tarifa social": ["F.42"],
        "interconexion": ["F.58"],
        "AIR": ["L.12"],
        "sunset clause": ["L.15"],
    }

    for term, refs in terminos_implicitos.items():
        refs_validos = [r for r in refs if r in all_ids]
        if refs_validos:
            if term not in terminos:
                terminos[term] = refs_validos
            else:
                terminos[term] = list(set(terminos[term] + refs_validos))

    lines = [
        "# GLOSARIO DERIVADO",
        f"# NP-GLOSARIO  v{data['meta']['version']}  {stamp_fuente(data)}",
        f"# Hash fuente: {hash_deterministic(elementos)}",
        "",
        "================================================================================",
        "1.  TERMINOS EXTRAIDOS AUTOMATICAMENTE DE ELEMENTOS.JSON",
        "================================================================================",
        "",
        f"**Total terminos:** {len(terminos)}",
        "",
    ]
    for term in sorted(terminos.keys()):
        refs = ", ".join(sorted(terminos[term]))
        lines.append(f"### {term}")
        lines.append(f"**Elementos relacionados:** {refs}")
        lines.append("")
    write_file(writer, out_path, "\n".join(lines))
    if not writer:
        print(f"  [OK] glosario-derivado.md ({len(terminos)} terminos)")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="Generador derivado del sistema NP v1.0.0-beta.1")
    parser.add_argument("--all", action="store_true", help="Generar todos los artefactos")
    parser.add_argument("--validate", action="store_true", help="Validar integridad de elementos.json")
    parser.add_argument("--check-narrativos", action="store_true", help="Verificar consistencia de documentos manuales")
    parser.add_argument("--dry-run", action="store_true", help="Simular generacion sin escribir a disco")
    parser.add_argument("--categorias", action="store_true", help="Generar categorias .md")
    parser.add_argument("--schema", action="store_true", help="Generar schema-norma.json")
    parser.add_argument("--sql", action="store_true", help="Generar modelo-relacional.sql")
    parser.add_argument("--ficha", action="store_true", help="Generar ficha-norma.md")
    parser.add_argument("--matriz", action="store_true", help="Generar matriz-interdependencia.md")
    parser.add_argument("--glosario", action="store_true", help="Generar glosario-derivado.md")
    args = parser.parse_args()

    if not any([args.all, args.validate, args.check_narrativos, args.dry_run,
                args.categorias, args.schema, args.sql, args.ficha, args.matriz, args.glosario]):
        parser.print_help()
        return

    print(f"=== GENERADOR NP v1.0.0-beta.1 ===")
    print(f"Fuente: {DATA_PATH}")
    print(f"Salida: {OUTPUT_DIR}")
    print("")

    data = cargar_elementos()
    stats = get_stats(data["elementos"])
    print(f"Elementos: {stats['total_elementos']} | Categorias: {stats['categorias']} | Fases: {stats['fases_lectura']}")
    print("")

    # Modo validacion
    if args.validate:
        ok, errores, warnings = validar_ssot(data, verbose=True)
        if not ok:
            print("VALIDACION FALLIDA. No se generaran artefactos.")
            sys.exit(1)
        print("VALIDACION OK. Fuente de verdad consistente.")
        print("")
        if not any([args.all, args.categorias, args.schema, args.sql, args.ficha, args.matriz, args.glosario]):
            return

    # Modo check narrativos
    if args.check_narrativos:
        ok, issues = check_narrativos(data, verbose=True)
        if not ok:
            print("CHECK NARRATIVOS: Issues detectados. Revisar documentos manuales.")
        else:
            print("CHECK NARRATIVOS: OK. Documentos manuales consistentes con fuente.")
        print("")
        if not any([args.all, args.categorias, args.schema, args.sql, args.ficha, args.matriz, args.glosario]):
            sys.exit(0 if ok else 1)

    # Validacion implicita antes de generar
    if not args.validate and any([args.all, args.categorias, args.schema, args.sql, args.ficha, args.matriz, args.glosario]):
        ok, errores, warnings = validar_ssot(data, verbose=False)
        if not ok:
            print("VALIDACION IMPLICITA FALLADA. Ejecute --validate para ver detalles.")
            sys.exit(1)

    writer = get_writer(args.dry_run)

    if args.all or args.categorias:
        print("[1/6] Generando categorias .md...")
        generar_categorias(data, writer)

    if args.all or args.schema:
        print("[2/6] Generando schema-norma.json...")
        generar_schema(data, writer)

    if args.all or args.sql:
        print("[3/6] Generando modelo-relacional.sql...")
        generar_sql(data, writer)

    if args.all or args.ficha:
        print("[4/6] Generando ficha-norma.md...")
        generar_ficha(data, writer)

    if args.all or args.matriz:
        print("[5/6] Generando matriz-interdependencia.md...")
        generar_matriz(data, writer)

    if args.all or args.glosario:
        print("[6/6] Generando glosario-derivado.md...")
        generar_glosario(data, writer)

    if writer:
        writer.report()
        print("=== DRY RUN COMPLETADO (sin escritura) ===")
    else:
        print("")
        print("=== GENERACION COMPLETADA ===")

if __name__ == "__main__":
    main()
