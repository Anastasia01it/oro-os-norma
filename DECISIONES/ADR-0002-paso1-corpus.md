# ADR-0002 — Paso 1: manifiesto de integridad + índice FTS5 del corpus

- **Fecha:** 2026-09-23
- **Estado:** IMPLEMENTADO (todas las pruebas en verde)
- **Alcance:** corpus = `normas_procesar/*.md` — 90 archivos, 21,659,798 bytes
  (el usuario movió las normas del raíz a `normas_procesar/`; verificado este paso)
- **Desviación de ruta respecto al plan:** manifiesto en `normas_procesar/manifest.json`
  (en lugar de raíz) e índice en `sistema/data/corpus.index.sqlite`. Razón: el sello viaja
  con su corpus; `sistema/` concentra la infraestructura. Sin coste; documentado.

## Qué se construyó

1. `sistema/scripts/build_manifest.py` → `normas_procesar/manifest.json`
   (SHA-256 por archivo + `set_hash` = sha256 del listado nombre:hash ordenado).
2. `sistema/scripts/build_index.py` → `sistema/data/corpus.index.sqlite`
   - Pre-condición fail-closed: si el corpus diverge del manifiesto, NO indexa.
   - Segmentación por encabezados Markdown (lossless: concatenar chunks reproduce el archivo;
     1.811 chunks en 90 documentos).
3. `sistema/scripts/integrity_check.py` — sello anti-alteración (ítem 29 del plan).
4. `sistema/scripts/differential_check.py` — calidad del índice (ítem 21 del plan).

Cero dependencias externas (solo stdlib Python): decisión métrica S (superficie de dependencia).

## Resultados de las pruebas (reproducibles)

| Chequeo | Resultado |
|---|---|
| Validación contra manifiesto antes de indexar | OK (sin divergencias) |
| Cobertura índice == disco == manifiesto | OK |
| Reconstrucción lossless (SHA-256 desde chunks) | 0 fallos / 90 archivos |
| C1: FTS5 == tokenizador de referencia (fuerza bruta) | 30/30 triples (100%) |
| C2: FTS5 ⊆ ripgrep (triples ASCII, df 1..8) | 15/15 (100%) |
| integrity_check | OK, set_hash `ed71c7223adca6c2…` |

## Hallazgos de diseño (lecciones pagadas, quedan registradas)

1. **rg multilínea `-U` con patrón ordenado sub-reporta** coincidencias en algunos archivos
   grandes (5 archivos tenían co-ocurrencia real según SQL LIKE; rg -U solo halló 2).
   Consecuencia: el oráculo rg se usa solo en su modo robusto de token único, y la igualdad
   exacta se prueba contra un **tokenizador de referencia independiente** (\w+ Unicode +
   plegado NFKD, mismas reglas que unicode61). No usar rg -U como oráculo de benchmark.
2. **Contrato semántico explícito o el diferencial miente:** LIKE-substring ≠ token FTS
   (embeddings en palabra mayor); rg exacto ≠ FTS plegado (diacríticos). Cada par de motores
   exige un dominio restringido donde sus semánticas coinciden: C1 cubre todo el alfabeto
   (misma semántica por construcción), C2 se restringe a triples ASCII originales.
3. **El control diferencial también audita al auditor:** detectó dos bugs propios
   (muestreo por frecuencia invertida; flag `-U` no propagado) antes de tocar el índice.

## Cobertura del plan estructural con este paso

- **Cubierto (infraestructura):** ítems 2 (fuente de verdad delimitada + versión inicial),
  8/10 (memoria externa + recuperación selectiva con tope de presupuesto — pendiente el tope
  en `parametros.yml`, llega con M1), 21 (índice validado contra oráculo antes de confiar),
  29 (integridad por hash contra inyección/alteración), 25 (lo determinístico va a script —
  este paso es la demostración).
- **Parcial:** ítem 16 (evidencia referenciará `corpus_hash`: el hash existe por archivo y de
  conjunto; la exigencia llega con M1/piloto), ítem 34 (manifiesto + resultados registrados;
  falta `runs/<id>/manifest.json` del piloto).
- **Métricas del plan actualizadas:** cobertura de controles implementados: paso 1 de 5
  casillas del checklist §5 de SOLUCION-PLAN-ESTRUCTURAL (marcada).

## Consecuencias

- Toda corrida sensible del procesador debe exigir `integrity_check.py` en verde (regla
  operativa documentada en `sistema/README.md`).
- El índice FTS5 queda disponible para el paso 3 (M1: evidencia obligatoria) y el piloto
  (paso 5): la recuperación selectiva ya no es una promesa, es una consulta SQL.

## Disparadores de re-evaluación registrados

- Corpus > ~500 normas o consultas > 2 s → re-evaluar almacén (SQLite vs PostgreSQL,
  ADR-0001 §6).
- Hallazgo 1 (rg -U) se re-verifica si se actualiza ripgrep de versión mayor.
