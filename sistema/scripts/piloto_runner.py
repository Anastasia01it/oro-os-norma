#!/usr/bin/env python3
"""Director del piloto M6 v0 — conduce la lectura de la norma por entregas.

Principio (diseno aprobado): la IA lectora es una FUNCION SIN MEMORIA. El
director (este script) posee todo el estado: que fragmento toca, que campos se
exigen, presupuestos, validacion, persistencia y reanudacion. La norma entera
JAMAS entra en contexto: solo la entrega acotada de la tarea en curso.

Comandos:
  init      — sella el corpus, descubre anclas, arma el plan de tareas, crea ficha/registro
  next      — imprime la entrega actual (objetivos + texto acotado) como JSON
  submit    — lee sistema/piloto/respuesta.json, valida, fusiona en ficha, avanza
  estado    — resumen de avance y presupuesto
  cerrar    — valida ficha, puntua el oro, corre la puerta, emite certificado

Reanudacion: todo estado vive en sistema/piloto/*.json/jsonl; una sesion nueva
(siquiera compactada o de otra herramienta) continua con 'next' sin perdida.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
PILOTO_DIR = os.path.join(ROOT, "sistema", "piloto")
CORPUS_DIR = os.path.join(ROOT, "normas_procesar")
MANIFEST_PATH = os.path.join(CORPUS_DIR, "manifest.json")
DATA_NP = os.path.join(ROOT, "procesador", "v1.0.0-beta.1", "data", "elementos.json")
VALIDADOR = os.path.join(ROOT, "procesador", "v1.0.0-beta.1", "scripts", "validar-ficha.py")
INTEGRIDAD = os.path.join(SCRIPT_DIR, "integrity_check.py")

NORMA = "LEY-142-1994.md"
ID_FICHA = "NP-FICHA-LEY-142-1994-001"
FASES_PILOTO = [0, 1, 2, 8]
TOPE_CARACTERES_ENTREGA = 30000  # ~7.5k tokens por entrega: presupuesto duro
ESTADO_PATH = os.path.join(PILOTO_DIR, "run-state.json")
FICHA_PATH = os.path.join(PILOTO_DIR, "ficha.json")
REGISTRO_PATH = os.path.join(PILOTO_DIR, "registro.jsonl")
RESPUESTA_PATH = os.path.join(PILOTO_DIR, "respuesta.json")
RESPUESTAS_ORO_PATH = os.path.join(PILOTO_DIR, "respuestas-oro.json")

CITA_RX = re.compile(r"^([^\n]+?\.md)#L(\d+)(?:-L(\d+))?$")
BOGOTA = timezone(timedelta(hours=-5))


def ahora():
    return datetime.now(BOGOTA).strftime("%Y-%m-%dT%H:%M:%S%z")


def fold(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def plano(s):
    return re.sub(r"\s+", " ", s).strip()


def sh(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cargar_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def log(reg):
    with open(REGISTRO_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- init
def verificar_corpus():
    r = subprocess.run([sys.executable, INTEGRIDAD], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout + r.stderr)
        raise SystemExit("CORPUS NO INTEGRO. La puerta no abre: no se inicia el piloto.")
    manifest = cargar_json(MANIFEST_PATH)
    entrada = manifest["files"].get(NORMA)
    if not entrada:
        raise SystemExit(f"{NORMA} no esta en el manifiesto del corpus.")
    ruta = os.path.join(CORPUS_DIR, NORMA)
    with open(ruta, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != entrada["sha256"]:
        raise SystemExit(f"Hash de {NORMA} no coincide con el manifiesto.")
    return manifest


def descubrir_anclas(lineas):
    """Localiza secciones por patron (determinista, sin lineas fijas)."""
    def buscar(rx, grupo=0):
        rx = re.compile(rx, re.I)
        for i, l in enumerate(lineas, 1):
            if rx.search(l):
                return i
        # el patron puede cruzar un salto de linea (texto cortado en renglones)
        for i in range(len(lineas) - 1):
            if rx.search(plano(lineas[i] + " " + lineas[i + 1])):
                return i
        return None

    n = len(lineas)
    return {
        "portada": (1, 27),
        "art1": (buscar(r"^\*\*ARTÍCULO 1\."), buscar(r"^\*\*ARTÍCULO 2\.")),
        "art2": (buscar(r"^\*\*ARTÍCULO 2\."), buscar(r"^\*\*ARTÍCULO 3\.")),
        "art86": (buscar(r"^\*\*ARTÍCULO 86\."), buscar(r"^\*\*ARTÍCULO 89\.")),
        "art155": (buscar(r"^\*\*ARTÍCULO 155\."), buscar(r"^\*\*ARTÍCULO 156\.")),
        "derogado_ej": (buscar(r"Derogado por el art\. 7, Ley 286"), None),
        "suprime_ej": (buscar(r"Suprime parcialmente"), None),
        "disclaimer": (buscar(r"no se hace responsable de la vigencia"), None),
        "cierre": (max(1, n - 40), n),
    }


def conteo(lineas, patron):
    rx = re.compile(patron, re.I)
    return sum(1 for l in lineas if rx.search(fold(l)))


def construir_plan(lineas, anclas, elementos):
    def rango(nombre, a, b):
        aa = a or 1
        bb = (b - 1) if b else min(len(lineas), aa + 25)
        return [max(1, aa), min(len(lineas), bb)]

    por_fase = {f: [e for e in elementos if e["fase_lectura"] == f] for f in FASES_PILOTO}
    ex = anclas

    def fragmentos(*nombres):
        out = []
        for nm in nombres:
            a, b = ex[nm]
            if a:
                out.append([a, b if b else min(len(lineas), a + 2)])
        return sorted(out)

    estructura = {
        "articulos_numerados": conteo(lineas, r"^\*\*articulo\s+\d+\."),
        "titulos": conteo(lineas, r"^### titulo"),
        "capitulos": conteo(lineas, r"^#### capitulo"),
        "menciones_paragrafo": conteo(lineas, "paragrafo"),
        "articulos_nuevo": conteo(lineas, r"^\*\*articulo nuevo"),
        "anotaciones_derogada": conteo(lineas, "derogad"),
        "anotaciones_suprime": conteo(lineas, "suprime"),
        "disposiciones": conteo(lineas, r"disposiciones?\s+(adicional|transitoria|derogatoria|final)"),
    }

    tareas = [
        {"id": "T01", "fase": 0, "titulo": "Proposito del analisis",
         "objetivos": [e["id"] for e in por_fase[0]],
         "fragmentos": fragmentos("portada")},
        {"id": "T02", "fase": 1, "titulo": "Identificacion formal (A)",
         "objetivos": [e["id"] for e in por_fase[1] if e["id"].startswith("A.")],
         "fragmentos": fragmentos("portada", "art1")},
        {"id": "T03", "fase": 1, "titulo": "Estructura formal (B) — conteos computados por el director",
         "objetivos": [e["id"] for e in por_fase[1] if e["id"].startswith("B.")],
         "fragmentos": fragmentos("portada", "art1"),
         "datos_computados": estructura},
        {"id": "T04", "fase": 1, "titulo": "Jerarquia y validez (I)",
         "objetivos": [e["id"] for e in por_fase[1] if e["id"].startswith("I.")],
         "fragmentos": fragmentos("art2", "portada")},
        {"id": "T05", "fase": 2, "titulo": "Vigencia y estados (C)",
         "objetivos": [e["id"] for e in por_fase[2] if e["id"].startswith("C.")],
         "fragmentos": fragmentos("disclaimer", "derogado_ej", "suprime_ej", "cierre"),
         "datos_computados": {k: estructura[k] for k in
                              ("anotaciones_derogada", "anotaciones_suprime", "articulos_nuevo")}},
        {"id": "T06", "fase": 2, "titulo": "Eficacia y aplicabilidad (K)",
         "objetivos": [e["id"] for e in por_fase[2] if e["id"].startswith("K.")],
         "fragmentos": fragmentos("art1", "cierre", "disclaimer")},
        {"id": "T07", "fase": 8, "titulo": "Analisis economico / tarifario (L)",
         "objetivos": [e["id"] for e in por_fase[8]],
         "fragmentos": fragmentos("art86", "art155", "portada")},
        {"id": "T08", "fase": "oro", "titulo": "Respuestas al set de oro (25 casos)",
         "objetivos": [],
         "fragmentos": []},
    ]
    for t in tareas:
        t["cursor"] = 0
        t["entregas"] = 0
    return tareas


def cmd_init(reiniciar=False):
    if os.path.exists(ESTADO_PATH) and not reiniciar:
        raise SystemExit("Ya existe run-state.json. Reanude con 'next' o use --reiniciar.")
    manifest = verificar_corpus()
    elementos = cargar_json(DATA_NP)["elementos"]
    ruta = os.path.join(CORPUS_DIR, NORMA)
    with open(ruta, encoding="utf-8") as f:
        lineas = f.read().split("\n")
    anclas = descubrir_anclas(lineas)
    faltan = [k for k, v in anclas.items() if v[0] is None]
    if faltan:
        raise SystemExit(f"Anclas no localizadas (corpus distinto al esperado): {faltan}")
    tareas = construir_plan(lineas, anclas, elementos)

    os.makedirs(PILOTO_DIR, exist_ok=True)
    estado = {
        "piloto": "M6 v0.1 — vertical: fases 0,1,2,8 + oro",
        "norma": NORMA,
        "iniciado": ahora(),
        "tarea_idx": 0,
        "tareas": tareas,
        "presupuesto": {"entregas": 0, "caracteres_entregados": 0},
        "decisiones": [],
    }
    guardar_json(ESTADO_PATH, estado)
    ficha = {
        "meta": {
            "id_ficha": ID_FICHA,
            "version": "1.0.0-beta.1",
            "fecha_analisis": ahora(),
            "analista": "k2p6 (piloto v0, IA conductida por piloto_runner.py)",
            "organizacion": "piloto Norma",
            "proposito": "Demostrar lectura por entregas con evidencia obligatoria (M1) y medir contra el oro",
            "estado": "en_progreso",
            "norma_archivo": NORMA,
            "corpus_set_hash": manifest["set_hash"],
        },
        "fases": {},
        "evidencia": [],
    }
    guardar_json(FICHA_PATH, ficha)
    open(REGISTRO_PATH, "w").close()
    print("PILOTO INICIADO")
    print(f"Norma: {NORMA} ({len(lineas)} lineas) | sello: {manifest['set_hash'][:16]}…")
    print(f"Tareas: {len(tareas)} (fases {FASES_PILOTO} + oro)")
    print(f"Presupuesto por entrega: {TOPE_CARACTERES_ENTREGA} caracteres (~{TOPE_CARACTERES_ENTREGA//4} tokens)")
    print("Reanudacion en cualquier momento: python3 piloto_runner.py next")


# ---------------------------------------------------------------- next
def leer_fragmento(lineas, frag, tope):
    a, b = frag
    texto = "\n".join(f"{i}\t{lineas[i-1]}" for i in range(a, b + 1))
    return texto[:tope], len(texto)


def cmd_next():
    estado = cargar_json(ESTADO_PATH)
    lineas = open(os.path.join(CORPUS_DIR, NORMA), encoding="utf-8").read().split("\n")
    tarea = estado["tareas"][estado["tarea_idx"]]
    entrega = {"tarea": tarea["id"], "titulo": tarea["titulo"], "fase": tarea["fase"],
               "avance": f"{estado['tarea_idx']+1}/{len(estado['tareas'])}"}
    if tarea["fase"] == "oro":
        oro = cargar_json(os.path.join(ROOT, "sistema", "oro", "casos-oro.json"))
        entrega["instruccion"] = ("Responder las 25 preguntas del oro en sistema/piloto/respuestas-oro.json "
                                  "(formato: lista de {id, tipo_respuesta: afirmativa|ausente, respuesta, "
                                  "cita (o null), verbatim (o null), valor (solo conteos)}). "
                                  "Apoyese en la ficha construida y en consultas al indice; cite solo si verifico la linea.")
        entrega["preguntas"] = [{"id": c["id"], "pregunta": c["pregunta"]} for c in oro["casos"]]
        print(json.dumps(entrega, ensure_ascii=False, indent=2))
        return
    elementos = {e["id"]: e for e in cargar_json(DATA_NP)["elementos"]}
    objetivos = [{"campo": c, "nombre": elementos[c]["nombre"],
                  "ref_obligatorio": elementos[c]["requiere_ref_articulo"]} for c in tarea["objetivos"]]
    cuerpo, total = leer_fragmento(lineas, tarea["fragmentos"][tarea["cursor"]], TOPE_CARACTERES_ENTREGA)
    entrega["objetivos"] = objetivos
    entrega["fragmento"] = {"de": tarea["cursor"] + 1, "de_total": len(tarea["fragmentos"]),
                            "lineas": tarea["fragmentos"][tarea["cursor"]], "texto": cuerpo}
    if tarea.get("datos_computados") and tarea["cursor"] == 0:
        entrega["datos_computados"] = tarea["datos_computados"]
    entrega["contrato_respuesta"] = {
        "archivo": "sistema/piloto/respuesta.json",
        "formato": {"tarea": tarea["id"],
                    "extracciones": [{"campo": "…", "valor": "…", "ref_articulo": "…",
                                      "cita": f"{NORMA}#Ln" , "verbatim": "texto literal de esas lineas", "notas": "…"}],
                    "no_aplica": [{"campo": "…", "motivo": "…"}]},
        "reglas": ["TODO objetivo debe quedar en extracciones o en no_aplica (sin excepciones)",
                   "cita solo a lineas REALES del fragmento entregado; verbatim literal presente en ellas",
                   f"una extraccion por campo; las negativas (no encontrado) van en no_aplica"],
    }
    print(json.dumps(entrega, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- submit
def validar_respuesta(estado, tarea, resp, lineas, cobertura_completa, ya_en_ficha):
    errores = []
    if resp.get("tarea") != tarea["id"]:
        errores.append(f"tarea declarada {resp.get('tarea')!r} != {tarea['id']}")
    objetivos = set(tarea["objetivos"])
    vistos = set()
    for x in resp.get("extracciones", []):
        campo = x.get("campo")
        if campo not in objetivos:
            errores.append(f"{campo}: no es objetivo de {tarea['id']}")
            continue
        if campo in vistos:
            errores.append(f"{campo}: duplicado")
        vistos.add(campo)
        if not str(x.get("valor", "")).strip():
            errores.append(f"{campo}: valor vacio (use no_aplica si no aplica)")
        m = CITA_RX.match(str(x.get("cita", "")))
        if not m:
            errores.append(f"{campo}: cita invalida: {x.get('cita')!r}")
            continue
        if m.group(1) != NORMA:
            errores.append(f"{campo}: la cita debe ser a {NORMA}")
        l1, l2 = int(m.group(2)), int(m.group(3) or m.group(2))
        if not (1 <= l1 <= l2 <= len(lineas)):
            errores.append(f"{campo}: rango fuera de la norma ({len(lineas)} lineas)")
            continue
        trozo = "\n".join(lineas[l1 - 1:l2])
        if fold(plano(x.get("verbatim", ""))) not in fold(plano(trozo)):
            errores.append(f"{campo}: verbatim NO presente en {x.get('cita')}")
        elem = next(e for e in cargar_json(DATA_NP)["elementos"] if e["id"] == campo)
        if elem["requiere_ref_articulo"] and not str(x.get("ref_articulo", "")).strip():
            errores.append(f"{campo}: ref_articulo obligatorio para este elemento")
    for n in resp.get("no_aplica", []):
        campo = n.get("campo")
        if campo not in objetivos:
            errores.append(f"no_aplica {campo}: no es objetivo de {tarea['id']}")
            continue
        if campo in vistos:
            errores.append(f"no_aplica {campo}: ya respondido")
        vistos.add(campo)
        if not str(n.get("motivo", "")).strip():
            errores.append(f"no_aplica {campo}: motivo vacio")
    faltan = objetivos - vistos - ya_en_ficha
    if cobertura_completa and faltan:
        errores.append(f"objetivos sin respuesta: {sorted(faltan)}")
    return errores


def cmd_submit():
    estado = cargar_json(ESTADO_PATH)
    tarea = estado["tareas"][estado["tarea_idx"]]
    lineas = open(os.path.join(CORPUS_DIR, NORMA), encoding="utf-8").read().split("\n")
    resp = cargar_json(RESPUESTA_PATH)
    if tarea["fase"] == "oro":
        oro_errores = validar_respuestas_oro()
        if oro_errores:
            for e in oro_errores:
                print(f"  ❌ ORO: {e}")
            print("RESPUESTAS DE ORO INCOMPLETAS/INVALIDAS. Corrija sistema/piloto/respuestas-oro.json")
            log({"ts": ahora(), "tarea": "T08", "resultado": "oro-rechazada", "errores": oro_errores})
            sys.exit(1)
        estado["presupuesto"]["entregas"] += 1
        tarea["entregas"] += 1
        log({"ts": ahora(), "tarea": "T08", "resultado": "oro-aceptada",
             "respuestas": 25})
        estado["tarea_idx"] += 1
        guardar_json(ESTADO_PATH, estado)
        print("TAREA T08 CERRADA: 25 respuestas de oro registradas. Plan completo: cierre con 'cerrar'.")
        return
    if resp.get("solo_verificacion"):
        tarea["entregas"] += 1
        tarea["cursor"] += 1
        estado["presupuesto"]["entregas"] += 1
        log({"ts": ahora(), "tarea": tarea["id"], "entrega": tarea["entregas"],
             "resultado": "verificacion-sin-cambios"})
        avanza = tarea["cursor"] >= len(tarea["fragmentos"])
        if not avanza:
            guardar_json(ESTADO_PATH, estado)
            print(f"Fragmento verificado sin cambios. Quedan {len(tarea['fragmentos'])-tarea['cursor']} fragmento(s).")
            return
    else:
        ficha_previa = cargar_json(FICHA_PATH)
        fase_previa = ficha_previa["fases"].get(str(tarea["fase"]), {})
        ya_en_ficha = {c for c in tarea["objetivos"] if c in fase_previa}
        es_ultimo = tarea["cursor"] >= len(tarea["fragmentos"]) - 1
        errores = validar_respuesta(estado, tarea, resp, lineas, es_ultimo, ya_en_ficha)
        if errores:
            for e in errores:
                print(f"  ❌ {e}")
            print("RESPUESTA RECHAZADA. Corrija sistema/piloto/respuesta.json y repita submit.")
            log({"ts": ahora(), "tarea": tarea["id"], "entrega": tarea["entregas"] + 1,
                 "resultado": "rechazada", "errores": errores})
            sys.exit(1)

        ficha = cargar_json(FICHA_PATH)
        ficha["fases"].setdefault(str(tarea["fase"]), {})
        for x in resp.get("extracciones", []):
            ficha["fases"][str(tarea["fase"])][x["campo"]] = {
                "completado": True, "na": False, "valor": x["valor"],
                "ref_articulo": x.get("ref_articulo", ""), "notas": x.get("notas", "")}
            ficha["evidencia"].append({"campo": x["campo"], "cita": x["cita"],
                                       "tipo": x.get("tipo", "texto"),
                                       "verbatim": x["verbatim"]})
        for n in resp.get("no_aplica", []):
            ficha["fases"][str(tarea["fase"])][n["campo"]] = {
                "completado": False, "na": True, "valor": "", "ref_articulo": "",
                "notas": f"[no aplica] {n['motivo']}"}
        guardar_json(FICHA_PATH, ficha)

        estado["presupuesto"]["entregas"] += 1
        estado["presupuesto"]["caracteres_entregados"] += len(json.dumps(resp, ensure_ascii=False))
        tarea["entregas"] += 1
        avanza = True
        if tarea["fase"] != "oro":
            tarea["cursor"] += 1
            if tarea["cursor"] < len(tarea["fragmentos"]):
                avanza = False
        log({"ts": ahora(), "tarea": tarea["id"], "entrega": tarea["entregas"],
             "extracciones": len(resp.get("extracciones", [])),
             "no_aplica": len(resp.get("no_aplica", [])), "resultado": "aceptada"})

    if avanza:
        r = subprocess.run([sys.executable, VALIDADOR, FICHA_PATH], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout)
            print("VALIDADOR DE FICHA RECHAZO el avance. No se avanza de tarea.")
            log({"ts": ahora(), "tarea": tarea["id"], "resultado": "validador-bloqueo",
                 "salida": r.stdout[-500:]})
            guardar_json(ESTADO_PATH, estado)
            sys.exit(1)
        estado["tarea_idx"] += 1
        if estado["tarea_idx"] < len(estado["tareas"]):
            print(f"TAREA {tarea['id']} CERRADA y validada. Siguiente: {estado['tareas'][estado['tarea_idx']]['id']}")
        else:
            print(f"TAREA {tarea['id']} CERRADA. Plan completo: cierre con 'cerrar'.")
    else:
        print(f"Entrega de {tarea['id']} aceptada. Quedan {len(tarea['fragmentos'])-tarea['cursor']} fragmento(s) de la misma tarea.")
    guardar_json(ESTADO_PATH, estado)


def cmd_corregir():
    """Errata del piloto: corrige campos de cualquier fase YA entregada, contra
    evidencia nueva. Cada correccion queda en registro.jsonl (auditabilidad):
    el piloto no borra errores, los corrige con comprobante."""
    resp = cargar_json(RESPUESTA_PATH)
    if resp.get("tipo") != "correccion":
        raise SystemExit("respuesta.json debe tener {\"tipo\": \"correccion\", \"items\": [...]}")
    lineas = open(os.path.join(CORPUS_DIR, NORMA), encoding="utf-8").read().split("\n")
    elementos = {e["id"]: e for e in cargar_json(DATA_NP)["elementos"]}
    ficha = cargar_json(FICHA_PATH)
    ficha["fases"].setdefault
    corregidos, errores = [], []
    for it in resp.get("items", []):
        campo = it.get("campo", "")
        elem = elementos.get(campo)
        if not elem:
            errores.append(f"{campo}: no existe en la taxonomia")
            continue
        m = CITA_RX.match(str(it.get("cita", "")))
        if not m or m.group(1) != NORMA:
            errores.append(f"{campo}: cita invalida o a otro archivo")
            continue
        l1, l2 = int(m.group(2)), int(m.group(3) or m.group(2))
        if not (1 <= l1 <= l2 <= len(lineas)):
            errores.append(f"{campo}: rango invalido")
            continue
        trozo = "\n".join(lineas[l1 - 1:l2])
        if fold(plano(it.get("verbatim", ""))) not in fold(plano(trozo)):
            errores.append(f"{campo}: verbatim NO presente en {it.get('cita')}")
            continue
        fase = str(elem["fase_lectura"])
        ficha["fases"].setdefault(fase, {})
        previo = ficha["fases"][fase].get(campo, {})
        ficha["fases"][fase][campo] = {
            "completado": True, "na": False, "valor": it["valor"],
            "ref_articulo": it.get("ref_articulo", ""), "notas": it.get("notas", "")}
        ficha["evidencia"].append({"campo": campo, "cita": it["cita"],
                                   "tipo": it.get("tipo", "texto"), "verbatim": it["verbatim"]})
        corregidos.append({"campo": campo, "antes": "na" if previo.get("na") else "valor-previo",
                           "cita": it["cita"]})
    if errores:
        for e in errores:
            print(f"  ❌ {e}")
        print("CORRECCION RECHAZADA (sin fusion).")
        sys.exit(1)
    guardar_json(FICHA_PATH, ficha)
    log({"ts": ahora(), "resultado": "correccion", "detalle": corregidos})
    print(f"CORRECCION APLICADA ({len(corregidos)} campos), con evidencia y bitacora:")
    for c in corregidos:
        print(f"  ✎ {c['campo']} ({c['antes']} → completado) {c['cita']}")


# ---------------------------------------------------------------- estado / cerrar
def cmd_estado():
    estado = cargar_json(ESTADO_PATH)
    print("=== ESTADO DEL PILOTO ===")
    print(f"Iniciado: {estado['iniciado']} | Norma: {estado['norma']}")
    print(f"Presupuesto: {estado['presupuesto']['entregas']} entregas | "
          f"{estado['presupuesto']['caracteres_entregados']:,} caracteres consumidos")
    for i, t in enumerate(estado["tareas"]):
        marca = "▶" if i == estado["tarea_idx"] else "✓" if i < estado["tarea_idx"] else "·"
        print(f" {marca} {t['id']} [fase {t['fase']}] {t['titulo']} ({t['entregas']} entregas)")


def validar_respuestas_oro():
    oro = cargar_json(os.path.join(ROOT, "sistema", "oro", "casos-oro.json"))["casos"]
    esperados = {c["id"]: c for c in oro}
    if not os.path.exists(RESPUESTAS_ORO_PATH):
        return ["falta sistema/piloto/respuestas-oro.json"]
    respuestas = cargar_json(RESPUESTAS_ORO_PATH)
    errores = []
    if not isinstance(respuestas, list):
        return ["respuestas-oro.json debe ser una lista"]
    vistos = set()
    for r in respuestas:
        rid = r.get("id")
        if rid not in esperados:
            errores.append(f"id desconocido: {rid!r}")
            continue
        vistos.add(rid)
        if r.get("tipo_respuesta") not in ("afirmativa", "ausente"):
            errores.append(f"{rid}: tipo_respuesta debe ser afirmativa|ausente")
        if esperados[rid]["verificacion"] == "ausente":
            if r.get("tipo_respuesta") != "ausente" or r.get("cita"):
                errores.append(f"{rid}: caso negativo exige tipo_respuesta=ausente y cita=null")
        elif r.get("tipo_respuesta") == "ausente":
            errores.append(f"{rid}: caso positivo respondido como ausente")
        if r.get("tipo_respuesta") == "afirmativa" and not str(r.get("respuesta", "")).strip():
            errores.append(f"{rid}: respuesta vacia")
    faltan = set(esperados) - vistos
    if faltan:
        errores.append(f"faltan respuestas: {sorted(faltan)}")
    return errores


def cmd_cerrar():
    estado = cargar_json(ESTADO_PATH)
    ficha = cargar_json(FICHA_PATH)
    ficha["meta"]["estado"] = "completada"
    ficha["meta"]["fecha_cierre"] = ahora()
    guardar_json(FICHA_PATH, ficha)
    print("=== CIERRE DEL PILOTO ===")
    r = subprocess.run([sys.executable, VALIDADOR, FICHA_PATH], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        raise SystemExit("FICHA RECHAZADA al cierre. No hay certificado.")

    puntaje = puntuar_oro()
    guardar_json(os.path.join(PILOTO_DIR, "puntaje-oro.json"), puntaje)
    print(f"\nORO: {puntaje['mecanicamente_correctas']}/{puntaje['total']} mecanicamente correctas | "
          f"{puntaje['pendientes_humanas']} respuestas citadas quedan para juicio humano")

    print("\n=== PUERTA ===")
    r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "puerta.py")])
    puerta = "ABIERTA" if r.returncode == 0 else f"CERRADA (exit {r.returncode})"
    cert = {
        "certificado": "PILOTO M6 v0.1",
        "fecha": ahora(), "norma": NORMA, "id_ficha": ID_FICHA,
        "ficha_validada": True, "oro": puntaje, "puerta": puerta,
        "presupuesto": estado["presupuesto"],
        "huella_ficha": sh(json.dumps(ficha, sort_keys=True, ensure_ascii=False)),
        "scope": estado["piloto"],
        "aceptacion_humana": "pendiente",
    }
    guardar_json(os.path.join(PILOTO_DIR, "certificado.json"), cert)
    print(f"\nCERTIFICADO: sistema/piloto/certificado.json | puerta: {puerta}")
    print("La aceptacion final del piloto es decision del humano (revisar ficha, puntaje y certificado).")


def puntuar_oro():
    oro = cargar_json(os.path.join(ROOT, "sistema", "oro", "casos-oro.json"))["casos"]
    respuestas = {r["id"]: r for r in cargar_json(RESPUESTAS_ORO_PATH)}
    lineas = open(os.path.join(CORPUS_DIR, NORMA), encoding="utf-8").read().split("\n")
    por_id = {c["id"]: c for c in oro}
    detalle, mec, hum = [], 0, 0
    for cid, caso in por_id.items():
        r = respuestas.get(cid)
        if not r:
            detalle.append({"id": cid, "estado": "SIN RESPUESTA"})
            continue
        if caso["verificacion"] == "ausente":
            ok = r.get("tipo_respuesta") == "ausente" and not r.get("cita")
            detalle.append({"id": cid, "estado": "correcta" if ok else "incorrecta",
                            "tipo": "negativo", "regla": "la respuesta declara ausencia y no cita nada"})
            mec += ok
        elif caso["verificacion"] == "conteo":
            ok = str(r.get("valor", "")).strip() == str(caso["esperado"]["valor"])
            detalle.append({"id": cid, "estado": "correcta" if ok else "incorrecta",
                            "tipo": "conteo", "respondido": r.get("valor"),
                            "esperado": caso["esperado"]["valor"]})
            mec += ok
        else:
            m = CITA_RX.match(str(r.get("cita", "")))
            cita_ok = False
            if m and m.group(1) == NORMA:
                l1, l2 = int(m.group(2)), int(m.group(3) or m.group(2))
                if 1 <= l1 <= l2 <= len(lineas):
                    trozo = "\n".join(lineas[l1 - 1:l2])
                    cita_ok = fold(plano(r.get("verbatim", ""))) in fold(plano(trozo))
            if cita_ok:
                detalle.append({"id": cid, "estado": "citada-y-resuelta", "tipo": "cita",
                                "nota": "juicio semantico (respuesta vs esperado) para el humano"})
                hum += 1
            else:
                detalle.append({"id": cid, "estado": "cita-invalida", "tipo": "cita"})
    return {"total": len(por_id), "mecanicamente_correctas": mec,
            "pendientes_humanas": hum, "detalle": detalle}


def main():
    ap = argparse.ArgumentParser(description="Director del piloto M6 v0")
    ap.add_argument("comando", choices=["init", "next", "submit", "corregir", "estado", "cerrar"])
    ap.add_argument("--reiniciar", action="store_true")
    args = ap.parse_args()
    {"init": lambda: cmd_init(args.reiniciar), "next": cmd_next, "submit": cmd_submit,
     "corregir": cmd_corregir, "estado": cmd_estado, "cerrar": cmd_cerrar}[args.comando]()


if __name__ == "__main__":
    main()
