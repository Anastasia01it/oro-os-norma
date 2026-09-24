# ADR-0007 — Verificación del corpus contra fuente primaria (método + primeros hallazgos)

- **Fecha:** 2026-09-23
- **Estado:** MÉTODO ADOPTADO (herramienta en el repo); correcciones al corpus
  **propuestas, pendientes de firma humana**
- **Contexto:** ADR-0001 registró como riesgo abierto que los 90 textos del
  corpus nunca fueron contrastados con la fuente oficial. Este ADR cierra el
  método y abre los resultados.

## Decisión

1. **El método de verificación es `sistema/scripts/verificar_fuente.py`**:
   comparación determinista, artículo a artículo, normalización fold+plano,
   umbral "casi" = 0.98, **fail-closed** (la duda se reporta como divergencia,
   nunca como match silencioso). Evidencia de cada divergencia: primer diff con
   contexto en ambos lados.
2. **Regla de aceptación propuesta**: una norma queda VERIFICADA cuando todo
   artículo de su corpus aparece en la fuente como exacto/casi y la cobertura
   de la captura es completa. Las divergencias se clasifican (ver README de
   `sistema/verificacion/`); solo "contenido_perdido" obliga a corregir el corpus.
3. **Corrección de contenido = errata con evidencia** (mismo mecanismo del
   piloto): se corrige el archivo del corpus desde la fuente oficial, se
   regenera el manifiesto (nuevo sello), commit que referencia el informe, y
   firma humana en este ADR. Nunca edición silenciosa: el historial debe poder
   contar qué cambió y por qué.

## Resultados del primer ciclo (2 casos completados, 1 norma piloto mapeada)

- **ley_1581_de_2012.md — NO VERIFICADA.** 28/30 artículos verificados.
  - **H1 (crítico):** el art. 26 del corpus está truncado: faltan los literales
    d), e), f) y los parágrafos 1o y 2o frente a la fuente oficial.
  - **H2 (documentar):** el art. 30 difiere solo en el bloque de sanción:
    el gestor CRA renderiza la sanción de 2012 (Barreras/Santos + nota C-748);
    el texto del corpus (proveniente de SUIN) renderiza otra presentación
    (Londoño Ulloa + Director DAFP). El cuerpo de la norma es idéntico.
- **resolucion_0412_de_2026.md — PARCIAL.** 20/21 artículos cubiertos
  verificados (17 exactos + 3 casi). Art. 21 divergente por formato de tabla.
  Arts. 22–50 quedaron sin cobertura porque la página oficial excede el límite
  de captura de 5 MB (no es divergencia: es deuda de captura).
  - Hallazgo adicional: **la fuente oficial misma** contiene una corrupción de
    texto ("Decreto 1381 de 20e incorporan…"). Se reporta al emisor; el corpus
    no debe heredarla ni "corregirla" por cuenta propia.
- **LEY-142-1994.md — PENDIENTE.** Fuente identificada en el gestor CRA;
  requiere captura por secciones o PDF (página > 5 MB).

## Lecciones de método (incorporadas a la herramienta)

- Los espejos oficiales (EVA/SUIN/Gestor CRA) tienen **aparatos de anotación
  distintos**: el corpus los trae en línea (Jurisprudencia, Concordancias,
  Texto del Proyecto de Ley Anterior); las páginas, en ventanas emergentes. La
  comparación debe remover el aparato, no compararlo.
- Las etiquetas de anotación llegan como texto suelto tras la conversión de
  enlaces `javascript:` — se eliminan completas.
- "Artículo CONDICIONALMENTE exequible" no abre artículo nuevo (falsa clave).
- Palabras de navegación cortas ("datos", "buscar") no pueden filtrarse por
  subcadena en texto legal: casi matan el art. 1o de la Ley 1581. Se filtran
  solo como línea corta exacta/prefijo (y el error restante inclina a
  NO_VERIFICADA, no a falso positivo).

## Alcance honesto

- 2 de 90 archivos verificados en este ciclo; 1 mapeado como pendiente; 87 con
  ruta de verificación identificada pero no ejecutada.
- Canales: gestor CRA y MinVivienda responden; Función Pública, SUIN y Senado
  bloquean al capturador desde este entorno (requieren canal alterno o
  verificación humana).
- La herramienta compara texto; no valida vigencia jurídica (eso sigue siendo
  juicio de abogado; las anotaciones de vigencia quedan fuera por diseño).

## Errata ejecutada (2026-09-23, aprobada por el humano)

**H1 corregido**: `normas_procesar/ley_1581_de_2012.md` art. 26 — se agregaron
los literales d), e), f) y los parágrafos 1o y 2o desde la fuente oficial
(captura: `sistema/verificacion/fuentes/ley_1581_2012.gestorcra.txt`). Tras la
corrección: 26 exactos + 3 casi = **29/30 artículos verificados**; la única
divergencia restante es H2 (bloque de sanción entre espejos oficiales, cuerpo
de la norma idéntico), aceptada como **excepción documentada** por decisión
humana: la norma se considera VERIFICADA_CON_EXCEPCION_DOCUMENTADA.
Sello del corpus regenerado (nuevo set_hash `aca446338f…` — el cambio de sello
ES la prueba de la corrección), índice reconstruido, puerta abierta.

## Lote CRA (15 resoluciones, 2026-09-23/24) — consolidado

Veredictos finales (detalle en `sistema/verificacion/ledger.json`):

- **VERIFICADA**: Res. 304-2004 (10/11), Res. 845-2018 (3/3).
- **VERIFICADA_CON_EXCEPCIONES**: Res. 0271-2003 (14/16, 2 divergencias documentadas en informe).
- **NO_VERIFICADA — fuente oficial en stub** (derogadas/integradas en la Res.
  943 de 2021; la página oficial ya no publica el texto): Res. 151-2001,
  351-2005, 720-2015, 778-2016. Parcial parecido: 0779-2016 (página solo con
  arts. 3o-4o). **Estas requieren verificación contra el Diario Oficial**
  (canal distinto al gestor).
- **NO_VERIFICADA — aparato de anotaciones / palabras pegadas**: Res. 1011-2025
  (25/38 verificados), 688-2014 (23/48), 376-2006, 894-2019, y **Res.
  0853-2018** (106 casi + 22 divergentes, todos por la misma causa mecánica:
  la conversión original pegó palabras en las juntas de anotaciones,
  "2015Establecer"). El contenido está; la errata es mecánica y espera
  aprobación humana por lote.
- **Requieren método nuevo**: Res. 943-2021 (resolución-compilación, 591
  artículos decimales; necesita comparación por secciones) y Res. 1027-2026
  (corpus por OCR con artículos en palabras — "Artículo Primero").

### Endurecimiento del comparador (lecciones del lote)

1. **Nunca filtrar por palabras sueltas de navegación** ("datos" mató el art.
   1o de la Ley 1581): solo frases seguras, o líneas cortas exactas.
2. **Índice de grupo**: al añadir un grupo de captura a la regex del
   segmentador, `m.group(1)` pasó a ser la palabra "Artículo" — un subagente
   lo detectó y murió a mitad del arreglo. Lección: prueba de humo automática
   tras tocar regex (ahora: las claves deben ser numéricas).
3. **Ordinales**: "ARTÍCULO 1o" (oficial) vs "ARTÍCULO 1" (corpus) no
   emparejaban aun con texto idéntico → clave canónica numérica (`norm_key`).
4. **Envolturas duras**: líneas que empiezan con "artículo" en minúscula son
   referencias cruzadas cortadas, no encabezados → el segmentador exige
   mayúsculas o tipo título.
5. **Escala**: difflib es cuadrático; para segmentos >100k caracteres el ratio
   usa 5 ventanas fijas deterministas (subestima → fail-closed).
6. **Los espejos oficiales cambian**: 4 resoluciones CRA ya no publican texto
   (stub de derogación). Verificar contra el gestor tiene fecha de caducidad;
  el Diario Oficial es la fuente primaria de respaldo.

## Matriz de canales de fuente oficial (2026-09-24, probada desde el entorno)

| Canal | Estado | Uso |
|---|---|---|
| normas.cra.gov.co/gestor | ✅ accesible | principal (leyes, decretos, resoluciones CRA) |
| minvivienda.gov.co | ✅ accesible | decretos/lineamientos del sector |
| web.archive.org (copia histórica del sitio oficial) | ✅ accesible | texto íntegro de páginas oficiales convertidas en stub |
| suin.gov.co, funcionpublica.gov.co, secretariasenado.gov.co | ❌ WAF | requieren otro entorno |
| diariooficial.gov.co | ❌ DNS inexistente | — |
| imprenta.gov.co (Imprenta Nacional) | ⚠️ responde pero es cascarón JS sin contenido scrapeable | solo con descarga manual de PDFs por humano |
| es.presidencia.gov.co / secretariajuridica (IP) | ❌ no responde | — |
| curl directo desde bash | ✅ funciona (corrije supuesto previo de "sin red") | capturas completas sin tope de 5 MB; convertir con `sistema/verificacion/html_a_texto.py` |

**Resultado lote stubs vía Wayback (2026-09-24)**: las 5 resoluciones con
fuente viva en stub se verificaron contra capturas históricas del propio
gestor (fechas snapshot en el ledger). 151-2001: 281 exactos/18 casi
(mayoría confirmada; resto por anotaciones de otra fecha + segmentos
corruptos del propio gestor). 351-2005: mayoría verificada (7/8/7).
0779-2016: verificada en la práctica (única diferencia = mueble de pie).
720-2015 y 778-2016: divergencia SISTÉMICA — el corpus llegó DEPURADO de
anotaciones inline y la fuente las trae → todos los artículos "divergen"
aun con cuerpo idéntico.

**Clase nueva: `corpus_depurado_vs_fuente_anotada`.** El corpus tiene dos
convenciones (con/sin anotaciones inline). **PROPUESTA D8 (pendiente de
firma)**: modo "cuerpo normativo" que retira spans de anotación `<...>` de
ambos lados antes de comparar (determinista, con bitácora de lo retirado).
Con D8 firmado se re-verifican 720/778 y se re-evalúan las NO_VERIFICADA
por anotaciones.

## Pendientes de decisión humana (actualizado)

1. ~~Aprobar la corrección del H1~~ — **HECHO 2026-09-23**.
2. ~~Errata mecánica por lote (palabras pegadas)~~ — **HECHO 2026-09-24**
   (391 ocurrencias en 26 archivos; bitácora en
   `informes/errata-pegados.jsonl`; además `limpiar` ya no pega palabras al
   quitar negritas; sellos regenerados; PUERTA ABIERTA).
3. **Firmar D5** (archivo histórico = fuente de respaldo; evidencia ya
   recolectada para los 5 stubs).
4. ~~Canal Diario Oficial~~ — **AGOTADO** automatizado; queda descarga
   manual de PDFs y verificación local.
5. ~~Lote leyes y decretos~~ — **HECHO 2026-09-24** (23 archivos; ledger
   41/90 rastreados).
6. **Firmar D6** (capturas por secciones: Decretos 1076/1077, ~4-5 MB).
7. **Firmar D7** (clase divergencia_administrativa: bloques de firmas/fechas
   cuando el cuerpo sea exacto/casi).
8. **Firmar D8** (modo cuerpo normativo: retirar anotaciones de ambos lados;
   desbloquea 720/778 y re-evalúa anotaciones en general).
9. **Errata Ley 632-2000**: decodificar entidades HTML (mecánica; misma
   regla de aprobación por lote que la errata anterior).
10. **Re-procesar corpus crudos**: Ley 253-1996 y Ley 1196-2008 (sin
    segmentación de artículos → no verificables como están).
11. **Análisis dedicado**: Constitución (367 div. por formato) y Ley 142-1994
    (ley madre, 119 div.) — artículo por artículo.
12. **Método para OCR y resoluciones-compilación** (1027-2026, 943-2021).
6. **Método para OCR y para resoluciones-compilación** (1027-2026, 943-2021)
   antes de verificarlas.
2. **Lote siguiente de verificación** (recomendado: las 13 resoluciones CRA,
   todas detrás del gestor accesible).
3. **Canal para SUIN/Función Pública/Senado** (descarga directa, otra red, o
   aceptación de verificación humana puntual).
4. **¿Corrección de la corrupción de la fuente oficial** (Res. 0412)? Se
   reporta a la CRA/MinVivienda; el corpus mantiene su texto hasta tener
   fuente correcta.
