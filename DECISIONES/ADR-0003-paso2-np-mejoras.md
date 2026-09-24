# ADR-0003 — Paso 2: M2 + M3 en Normativa-Procesador (cierra F-1 y F-2)

- **Fecha:** 2026-09-23
- **Estado:** IMPLEMENTADO (todas las pruebas en verde)
- **Alcance:** `procesador/v1.0.0-beta.1/scripts/generador.py` + 4 documentos narrativos del paquete.
  La fuente `data/elementos.json` NO se tocó: el hash fuente `cd28f9451bceeab2` se mantiene.

## Qué se cambió y por qué

### M3 — Reproducibilidad byte-exacta (cierra hallazgo F-1 de ADR-0001)

- **Antes:** los 5 artefactos generados llevaban marca de reloj de pared (`now_iso()`),
  así que cada regeneración difería en bytes aunque la fuente no cambiara.
- **Ahora:** `stamp_fuente(data)` usa `meta.fecha` de la fuente. La marca amarra cada
  artefacto a la versión exacta de su origen (coherente con P7, SSOT) y la regeneración
  es determinista.
- **Prueba:** dos corridas consecutivas de `--all` → `diff -r` sin diferencias
  (BYTE-IDENTICAL). Marca observada: `2026-08-24T11:44:11-0500` == `meta.fecha`.

### M2 — Conteos numéricos vs fuente (cierra hallazgo F-2 de ADR-0001)

- **Antes:** `--check-narrativos` verificaba existencia (N001) y refs rotas (N002).
  Un documento con todas las refs sanas pero totales atrasados pasaba limpio
  (era exactamente el caso: HANDOFF decía 263, la fuente computa 268).
- **Ahora:** N003 compara **declaraciones de total del sistema** contra stats computados.
  Diseño deliberado:
  - Solo totales ("Total elementos:", tabla `| Elementos | N |`, "N fases"); los conteos
    por categoría ("Categoria: E (13 elementos)") y las sumas ("= 55 elementos") quedan
    fuera del alcance del chequeo.
  - Guarda de historial: líneas de changelog ("2026-08-23 v1.0.0-alpha.1 Creacion, 202
    elementos en 12 categorias") son registros legítimos del pasado y no se tocan.
  - BACKLOG.md se agregó a `NARRATIVOS` (el check cubre ahora 4 documentos; estaba
    fuera y su "Elementos totales | 263" era invisible para él).

## Evidencia del chequeo funcionando

Primera corrida de N003 (ya con patrones refinados): 5 issues reales detectados —
HANDOFF (263, 8 fases), BACKLOG (263), README (263, 8 fases). Correcciones honestas
aplicadas a los 4 documentos (263→268, 8→10 fases, "7 reglas"→"15 reglas", etiquetas
de versión alpha.2→beta.1 en encabezados). Segunda corrida: **0 issues / 4 archivos**.

Lección reforzada: un chequeo nuevo debe demostrar su poder detectando lo real antes
de dar verde (secuencia rojo→verde, no verde de entrada).

## Verificación completa del paquete tras los cambios

| Prueba | Resultado |
|---|---|
| `--validate` | OK (fuente consistente, 0 errores/0 warnings) |
| `--check-narrativos` | 0 issues / 4 archivos |
| `--all` × 2 + `diff -r` | byte-identical (M3) |

## Estado del backlog M1–M6 tras este paso

- ✅ M2 (este ADR), M3 (este ADR)
- ⏭ M1 (evidencia obligatoria en schema) — **siguiente: paso 3**
- ⏭ M4 (SQLite FTS5) — **ya cubierto por el paso 1** (`sistema/`, ADR-0002)
- ⏭ M5 (pruebas oro), M6 (conector IA via dsh) — pasos 4 y 5

## Consecuencias operativas

- Regenerar artefactos NP ya no ensucia diffs con marcas de tiempo: cualquier diff
  futuro en `output/` significa cambio real de contenido.
- Todo documento narrativo nuevo que declare totales del sistema entra en el alcance
  de N003 al incluirse en `NARRATIVOS`.
- Riesgo aceptado por escrito: N003 no detecta totales en prosa libre sin palabras
  clave ("hay un total de doscientos sesenta y ocho elementos" no se captura; el
  dominio de estos documentos usa dígitos, patrón observado). Si aparece prosa
  numérica, se amplía el patrón con evidencia.
