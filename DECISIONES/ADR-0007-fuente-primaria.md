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

## Pendientes de decisión humana

1. ~~Aprobar la corrección del H1~~ — **HECHO 2026-09-23** (errata aplicada y
   verificada; excepción H2 aceptada como documentada).
2. **Lote siguiente de verificación** (recomendado: las 13 resoluciones CRA,
   todas detrás del gestor accesible).
3. **Canal para SUIN/Función Pública/Senado** (descarga directa, otra red, o
   aceptación de verificación humana puntual).
4. **¿Corrección de la corrupción de la fuente oficial** (Res. 0412)? Se
   reporta a la CRA/MinVivienda; el corpus mantiene su texto hasta tener
   fuente correcta.
