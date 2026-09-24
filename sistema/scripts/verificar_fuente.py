#!/usr/bin/env python3
"""verificar_fuente.py — Compara un archivo del corpus contra su fuente primaria.

Uso:
    python3 sistema/scripts/verificar_fuente.py <corpus.md> <fuente.txt> [--umbral 0.98]

Metodo (todo deterministico, sin IA):
  1. Limpieza de cada lado: muebles de pagina (EVA/Gestor), enlaces markdown,
     lineas de navegacion, marcadores de formato.
  2. Normalizacion fold()+plano() (misma usada en todo el sistema).
  3. Segmentacion por articulo en ambos lados.
  4. Comparacion articulo a articulo: exacto | casi (>= umbral) | divergente.

Salida: informe en texto + JSON (sistema/verificacion/informes/<norma>.json).
Exit 0 solo si TODO articulo del corpus aparece en la fuente sin divergencias.
Fail-closed: la duda se reporta como divergencia, nunca como match silencioso.
"""
import argparse, json, re, sys, unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "normas_procesar"
INFORMES = ROOT / "sistema" / "verificacion" / "informes"

# Frases de mueble de pagina: seguras a cualquier longitud (nunca aparecen
# en texto legal real). OJO: nunca usar palabras sueltas como "datos" —
# el articulo 1o de la Ley 1581 las contiene en prosa legal.
JUNK_SUBSTR = [
    "gestor normativo", "eva - gestor", "ir al inicio", "javascript:",
    "jurisprudencia vigencia", "nota del editor", "linea anticorrupcion",
    "soy transparente", "correo institucional", "notificaciones judiciales",
    "ultima actualizacion", "control de versiones", "creditos y reserva",
    "sede principal", "horario de atencion", "atencion y servicios a la ciudadania",
    "transparencia y acceso a inform", "documentacion relacionada",
    "seccion del suin", "busqueda por fecha", "ver mas",
]
# Palabras de navegacion: SOLO si la linea completa es corta (<80) — una linea
# legal corta que las contenga cae tambien, pero eso inclina a NO_VERIFICADA
# (fail-closed), nunca a un falso positivo.
JUNK_CORTO = [
    "datos", "buscar", "indice", "memoria", "videos", "descargas", "notificaciones",
    "abogacia", "desarrollos", "modificaciones", "concordancias", "anotaciones",
    "imprimir", "sentencia", "fallo", "concepto", "providencia", "auto", "logo",
    "inicio", "modulo", "volver", "compartir", "saltar al contenido",
]
LINK_RX = re.compile(r"\[([^\]]*)\]\([^)]*\)")
ART_RX = re.compile(r"^\**\s*art[íi]culo\s+([0-9]+(?:o\b|°|\.)?|\d+\.\d+|[a-z]+)\b\.?", re.I | re.M)
# Bloques de anotacion del gestor/SUIN que el corpus trae en linea pero la
# pagina oficial muestra como ventanas emergentes. Comienzan en el marcador y
# corren hasta el siguiente encabezado estructural (articulo/titulo/capitulo/
# seccion/paragrafo); el contenido puede ser viñetas o texto libre (p.ej.
# "Texto del Proyecto de Ley Anterior" trae el articulo del proyecto original).
ANOTACION_RX = re.compile(
    r"^\s*\**\s*(jurisprudencia vigencia|concordancias|doctrina concordante|doctrina|"
    r"notas de vigencia|modificaciones|texto anterior|texto del proyecto(\s+de\s+ley\s+anterior)?|vigencia|interpretacion|"
    r"anexos? ejecutivos?)\s*:?\s*\**$", re.I)
STRUCT_RX = re.compile(
    r"^\s*(#{1,4}\s|\**\s*art[íi]culo\s+(\d|nuevo)\b|\**\s*(t[ií]tulo|cap[ií]tulo|"
    r"secci[oó]n|par[aá]grafo)\b)", re.I)


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def plano(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def limpiar(texto: str) -> str:
    lineas = []
    en_anotacion = False
    for ln in texto.split("\n"):
        if en_anotacion:
            if not STRUCT_RX.match(ln):      # contenido de la anotacion: se omite
                continue
            en_anotacion = False               # encabezado estructural: se procesa
        if ANOTACION_RX.match(ln):
            en_anotacion = True
            continue
        # enlaces javascript: (etiquetas de anotaciones del gestor/SUIN): fuera
        # completos — su texto ("Concordancias)", "Texto del Proyecto...") no es
        # texto legal, es mueble de las ventanas emergentes.
        ln = re.sub(r"\[[^\]]*\]\(javascript:[^)]*\)+", " ", ln, flags=re.I)
        ln = LINK_RX.sub(lambda m: m.group(1), ln)          # [x](url) -> x
        ln = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", ln)         # imagenes -> nada
        ln = re.sub(r"^\s*[-#*>]+\s*", "", ln)                # viñetas/encabezados/citas md
        if "|" in ln:                                        # tablas md: conservar contenido
            celdas = [c.strip() for c in ln.strip().strip("|").split("|")]
            if celdas and all(re.fullmatch(r":?-{2,}:?", c or "-") for c in celdas):
                ln = ""                                      # fila separadora: fuera
            elif celdas:
                ln = " ".join(c for c in celdas if c)
        ln = ln.replace("\\", "").translate({ord(c): "" for c in "*_<>~`"})
        f = fold(plano(ln))
        if not f or f in ("---",):
            continue
        if any(j in f for j in JUNK_SUBSTR):
            continue
        if len(f) < 80 and any(f == j or f.startswith(j + " ") or f.startswith(j + ":")
                               for j in JUNK_CORTO):
            continue
        if re.fullmatch(r"[\d\s]+", f):                        # numeros de pagina sueltos
            continue
        lineas.append(plano(ln))
    return "\n".join(lineas)


def norm_key(k: str) -> str:
    """Clave canonica de articulo: '1o', '1°', '1º.' y '1.' -> '1'; los
    decimales ('1.1.1') se preservan enteros. Sin esto, corpus y fuente
    no emparejan aunque el texto sea identico (hallazgo del lote CRA)."""
    k = k.rstrip(".")
    k = re.sub(r"^(\d+)[oO°º]$", r"\1", k)
    return k


def segmentar(texto_limpio: str):
    """Devuelve {id: [textos]} (lista: una clave puede repetirse en la fuente,
    p.ej. marcador INEXEQUIBLE + articulo real). Cabecera bajo '__cabecera__'."""
    segmentos = {"__cabecera__": [[]]}
    actual = "__cabecera__"
    for ln in texto_limpio.split("\n"):
        # Mayusculas (ARTICULO) o tipo titulo (Articulo) abren segmento; minusculas
        # no: son envolturas duras de referencias cruzadas ("...los arts. 5 y 6 del
        # articulo 2o de la Resolucion..." empieza linea al cortarse) -> claves falsas.
        m = re.match(r"^\s*(ART[ÍI]CULO|Art[íi]culo)\s+(\d\S{0,9}|nuevo)(?=[\.\s,:;]|$)", ln)
        if m:
            actual = norm_key(m.group(2))
            segmentos.setdefault(actual, []).append([])
        segmentos[actual][-1].append(ln)
    return {k: [plano(" ".join(s)) for s in v]
            for k, v in segmentos.items()
            if k == "__cabecera__" or any(l.strip() for s in v for l in s)}


def ratio_determinista(a: str, b: str) -> float:
    """Similitud 0..1 determinista y acotada en tiempo. Textos medianos: trozos
    posicionales (los iguales cuestan O(n), solo los distintos pagan difflib,
    acotado por TOPE^2). Textos enormes (>100k): 5 ventanas fijas de 4000
    caracteres (deterministas); es una aproximacion que tiende a SUBestimar
    la similitud (fail-closed) y solo se usa donde difflib seria impractico."""
    if a == b:
        return 1.0
    n = max(len(a), len(b), 1)
    if n > 100_000:
        W = 4000
        puntos = [0, n // 4, n // 2, (3 * n) // 4, max(0, n - W)]
        total, k = 0.0, 0
        for ini in puntos:
            x, y = a[ini:ini + W], b[ini:ini + W]
            if x == y:
                total += 1.0
            else:
                total += SequenceMatcher(None, x, y).ratio()
            k += 1
        return total / k
    TOPE = 8000
    total, peso = 0.0, 0
    for ini in range(0, n, TOPE):
        x, y = a[ini:ini + TOPE], b[ini:ini + TOPE]
        m = max(len(x), len(y))
        if m == 0:
            continue
        r = 1.0 if x == y else SequenceMatcher(None, x, y).ratio()
        total += r * m
        peso += m
    return total / peso if peso else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("fuente")
    ap.add_argument("--umbral", type=float, default=0.98)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args()

    corpus_raw = Path(args.corpus).read_text(encoding="utf-8", errors="replace")
    fuente_raw = Path(args.fuente).read_text(encoding="utf-8", errors="replace")

    seg_c = segmentar(limpiar(corpus_raw))
    seg_f = segmentar(limpiar(fuente_raw))
    arts_c = [k for k in seg_c if k != "__cabecera__"]

    informe = {"corpus": Path(args.corpus).name, "fuente": args.fuente,
               "umbral": args.umbral, "articulos_corpus": len(arts_c),
               "resultados": [], "sin_contraparte": [], "veredicto": None}

    def mejor_par(copias_c, copias_f):
        """Compara todas las copias de un articulo (lado corpus vs lado fuente);
        toma el mejor emparejamiento. Devuelve (estado, similitud, corpus, fuente).
        Para textos largos, la similitud se calcula sobre un prefijo acotado
        (difflib es cuadratico; un articulo de 100k caracteres agotaria el
        tiempo). La igualdad exacta siempre se chequea completa."""
        best = None
        for a0 in copias_c:
            for b0 in copias_f:
                a, b = fold(a0), fold(b0)
                if a == b:
                    return ("exacto", 1.0, a0, b0)
                r = ratio_determinista(a, b)
                if best is None or r > best[1]:
                    best = (None, r, a0, b0)
        r = best[1]
        return ("casi" if r >= args.umbral else "divergente", r, best[2], best[3])

    n_exactos = n_casi = n_div = 0
    for art in arts_c:
        copias_c = seg_c[art]
        copias_f = seg_f.get(art, [])
        if not copias_f:
            informe["resultados"].append({"articulo": art, "estado": "ausente_en_fuente"})
            n_div += 1
            continue
        estado, r, a0, b0 = mejor_par(copias_c, copias_f)
        if estado == "exacto":
            informe["resultados"].append({"articulo": art, "estado": "exacto"})
            n_exactos += 1
            continue
        sm = SequenceMatcher(None, fold(a0), fold(b0))
        diff = None
        if len(a0) + len(b0) <= 40000:           # difflib es cuadratico: acotar
            diff = next((op for op in sm.get_opcodes() if op[0] != "equal"), None)
        trozo = None
        if diff:
            _, i1, i2, j1, j2 = diff
            trozo = {"corpus": f"...{a0[max(0,i1-60):i2+60]}...",
                     "fuente": f"...{b0[max(0,j1-60):j2+60]}..."}
        informe["resultados"].append({"articulo": art, "estado": estado, "similitud": round(r, 4),
                                      "corpus": a0[:180], "fuente": b0[:180], "diff": trozo})
        n_casi += estado == "casi"
        n_div += estado == "divergente"

    informe["resumen"] = {"exactos": n_exactos, "casi": n_casi, "divergentes": n_div}
    informe["veredicto"] = "VERIFICADA" if n_div == 0 else "NO_VERIFICADA"
    informe["sin_contraparte"] = [k for k in seg_f if k != "__cabecera__" and k not in seg_c]

    print(f"== {informe['veredicto']} ==  {Path(args.corpus).name} vs fuente")
    print(f"articulos corpus: {len(arts_c)} | exactos: {n_exactos} | casi: {n_casi} | divergentes: {n_div}")
    for r in informe["resultados"]:
        if r["estado"] not in ("exacto",):
            print(f"  [{r['estado']}] articulo {r['articulo']}" + (f" sim={r.get('similitud')}" if "similitud" in r else ""))
            if r["estado"] == "divergente":
                print(f"     corpus: {r['corpus'][:140]}")
                print(f"     fuente: {r['fuente'][:140]}")
    if informe["sin_contraparte"]:
        print(f"en fuente pero no en corpus (anotaciones/extras, no afectan): {len(informe['sin_contraparte'])}")

    INFORMES.mkdir(parents=True, exist_ok=True)
    salida = args.salida or str(INFORMES / (Path(args.corpus).stem + ".json"))
    Path(salida).write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"informe: {salida}")
    sys.exit(0 if informe["veredicto"] == "VERIFICADA" else 1)


if __name__ == "__main__":
    main()
