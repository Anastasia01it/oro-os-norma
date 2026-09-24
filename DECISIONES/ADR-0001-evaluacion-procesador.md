# ADR-0001 — Evaluación de Normativa-Procesador v1.0.0-beta.1 (¿adoptar, mejorar o tomar como guía?)

- **Fecha:** 2026-09-23
- **Estado:** ACEPTADO (veredicto por componente; no monolítico)
- **Contexto:** paquete histórico `procesador/v1.0.0-beta.1.tar.gz`, desempaquetado en
  `procesador/v1.0.0-beta.1/`. Evaluado con la métrica de selección de
  `plan-estructural/SOLUCION-PLAN-ESTRUCTURAL.md` (V×3, F×3, D×2, A×2, G×2, E, S, L).
- **Qué es NP:** taxonomía de 268 elementos en 13 categorías (A-M) para caracterizar una
  norma jurídica, con generador determinista (SSOT), protocolo de lectura de 10 fases
  (P1-P7, R1-R15), schema de salida, DDL PostgreSQL (16 tablas) y plantilla ELI/LexML.
  **Versión humana-pura por diseño**; el conector AI era la v2.0 planeada (nunca construida).

## 1. Pruebas ejecutadas (evidencia, no impresiones)

| # | Prueba | Comando | Resultado |
|---|---|---|---|
| T1 | Validación SSOT (14 reglas) | `generador.py --validate` | **0 errores, 0 warnings** (268 elementos, 13 cat, 10 fases) |
| T2 | Coherencia de docs manuales | `generador.py --check-narrativos` | 134 refs, 0 issues **pero** ver F-2 |
| T3 | Reproducibilidad total | backup + `--all` + diff | **Contenido byte-por-byte idéntico** en los 19 artefactos; única diferencia: timestamps embebidos (F-1) |
| T4 | Dependencias | inspección de imports | **Solo stdlib Python** (json, argparse, hashlib…). Cero instalación |

## 2. Hallazgos

- **F-1 (menor):** la regeneración cambia únicamente fechas de generación embebidas en headers.
  Reproducibilidad exacta exigida por nuestro plan (ítem 15) requiere fix: inyectar fecha desde
  `meta` o flag `--no-stamp`.
- **F-2 (control parcial):** `HANDOFF.md` declara "263 elementos" (stale, de alpha.2; el SSOT tiene 268)
  y `--check-narrativos` **no lo detecta**: solo valida referencias rotas (`X.N`) y existencia de
  archivos, no conteos numéricos contra stats computados.
- **F-3 (paquete incompleto):** el tar no incluye `scripts/md_builder.py`, `docs/categorias/*.md`
  (13 manuales) ni `docs/auditoria-campo/` (2 auditorías de campo, 40 observaciones — la evidencia
  que validó los 61 elementos incorporados). Referenciados en HANDOFF pero ausentes.
- **F-4 (alcance, no defecto):** MANIFEST declara "Gaps: 0, listo para producción" — para **uso
  humano manual**. El conector AI no existe: es exactamente la pieza que aporta nuestro plan
  estructural con dsh.
- **F-5 (menor):** `schema-elementos.json` es JSON Schema **draft-07** con `format: date-time`;
  varios validadores ignoran `format` salvo configuración explícita (ajv). Subir a draft 2020-12
  en la mejora.

## 3. Matriz de evaluación por componente (0-2 por criterio; V y F son gates)

| Componente | V | F | D | A | G | E | S | L | Veredicto |
|---|---|---|---|---|---|---|---|---|---|
| **C1** SSOT: `elementos.json` + `schema-elementos.json` + `generador.py` | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **ADOPTAR** |
| **C2** `ESTRATEGIA.md` (fases, P1-P7, R1-R15) | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | **ADOPTAR como protocolo**, traducir a reglas operativas del agente |
| **C3** `schema-norma.json` + `ficha-norma.md` (salida, 268 campos) | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | **ADOPTAR + MEJORAR** (F: la REF. ARTÍCULO es opcional hoy) |
| **C4** `modelo-relacional.sql` (PostgreSQL, 16 tablas) | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | **REEMPLAZAR como runtime** (la métrica ya eligió SQLite FTS5); conservar como documento de modelo |
| **C5** Docs manuales (HANDOFF, BACKLOG, CIERRE, ELI/LexML) | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | **USAR como guía histórica**; el check vigente no cubre conteos (F-2) |

### Por qué NO "tomarlo solo como guía para construir uno nuevo"
Una taxonomía de 268 campos **ya validada por 2 auditorías de campo** (CRA y SSPD, 40
observaciones, 61 elementos nuevos incorporados) es evidencia pagada. Reconstruirla desde cero
duplicaría ese costo y produciría un modelo sin esa historia. El criterio económico de la métrica
(L + E + S) es claro: adoptar el activo validado y concentrar el esfuerzo en el conector que falta.

## 4. DECISIÓN

1. **ADOPTAR C1** como SSOT del modelo de extracción del procesador de normas. Toda modificación
   al modelo pasa por `elementos.json` + `--validate` (regla P7 ya existente, alineada con nuestro ítem 2).
2. **ADOPTAR C3** como schema de salida obligatorio del procesador, **con mejora M1**:
   evidencia obligatoria cuando `requiere_ref_articulo=true` (el gancho ya existe en el SSOT;
   hoy es opcional — se vuelve fail-closed en validación).
3. **ADOPTAR C2** traduciendo las 10 fases y R1-R15 al `AGENTS.md`/skill del agente (dsh),
   conservando P1-P7 como principios rectorerentes (P1/P2/P5 son, casi literalmente, nuestros
   ítems 1, 35 y 2 del plan estructural — convergencia independiente, señal de solidez).
4. **REEMPLAZAR C4 como runtime:** SQLite FTS5 (decisión previa ADR implícita de
   SOLUCION-PLAN-ESTRUCTURAL §1). El DDL PostgreSQL se conserva como documentación del modelo
   relacional con disparador de re-evaluación (ver §6).
5. **C5** queda como historia del proyecto; su contenido alimenta el ADR-0002 (memoria del
   procesador) cuando se active.

## 5. Mejoras concretas acordadas (backlog del backlog)

| # | Mejora | Esfuerzo | Cierra |
|---|---|---|---|
| M1 | Validador fail-closed: exige REF. ARTÍCULO + cita textual cuando `requiere_ref_articulo=true` | medio | ítems 1, 2, 12 del plan |
| M2 | Extender `--check-narrativos`: conteos numéricos vs stats computados (detecta F-2) | ~10 líneas | ítem 34 |
| M3 | Reproducibilidad byte-exacta: fecha desde `meta` o `--no-stamp` (cierra F-1) | menor | ítem 15 |
| M4 | Runtime store: SQLite FTS5 derivado del DDL (artículos del corpus) | medio | ítems 8, 10, 21 |
| M5 | Gold tests iniciales: reconstruir casos desde `docs/auditoria-campo/` (recuperar del repo original si existe) | medio | ítems 5, 12, 24 |
| M6 | Conector AI (la "v2" histórica) con dsh: recuperación FTS5 → llenado de ficha con citas → verificador ciego → validación schema + `evidencia/registro.jsonl` | grande | ítems 1, 13, 23, 24, 34 |

## 6. Consecuencias y disparadores de re-evaluación

- **Consecuencia:** el procesador hereda una taxonomía validada; nuestro esfuerzo se concentra
  en el 20% que falta (conector, evidencia estricta, tests) en vez del 80% ya hecho (modelo).
- **Disparadores:** (a) corpus supera ~500 normas → re-evaluar SQLite vs PostgreSQL (C4 vuelve a
  la mesa con la misma matriz); (b) aparece estándar jurídico estructurado mejor que ELI/LexML
  adoptado en Colombia → evaluar extensión del schema; (c) toda falla en producción → caso de oro
  nuevo + mejora, según el mecanismo de evolución del plan estructural.
- **Riesgo aceptado por escrito (M1 del plan):** F-3 — la evidencia de las auditorías de campo no
  está en el paquete; hasta recuperarla, los gold tests M5 partirán de casos reconstruidos con el
  humano, no de los 40 registros originales.

*Pruebas T1-T4 reproducibles; comandos en §1. Evaluador: agente dsh (k2p6) con supervisión humana pendiente.*
