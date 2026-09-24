# ADR-0006 — Paso 5: piloto M6 v0, IA real de extremo a extremo sobre la Ley 142

- **Fecha:** 2026-09-23
- **Estado:** PILOTO COMPLETADO — certificado emitido, aceptación humana pendiente
- **Alcance:** `sistema/scripts/piloto_runner.py` (director), `sistema/piloto/`
  (ficha, registro, respuestas de oro, puntaje, certificado, estado de corrida).

## Qué se demostró

**Lectura conductida de una norma real por IA, con evidencia obligatoria, sin que
la norma entera entrara jamás en contexto.** La IA lectora funcionó como función
sin memoria: el director (Python) poseyó todo el estado; la IA solo transformó
fragmentos acotados en extracciones citadas.

Métricas del piloto:

| Métrica | Valor |
|---|---|
| Fases cubiertas (vertical) | 0, 1, 2, 8 + set de oro |
| Campos de la ficha cubiertos | 106 (53 completados con evidencia + 53 no-aplica honestos) |
| Ficha final | **ACEPTABLE: 53/53 afirmaciones comprobables contra el corpus** |
| Oro | 9/9 mecanicamente puntuables correctas (4 conteos + 5 negativos); 16 citadas y resueltas, juicio semántico para el humano |
| Texto de la norma entregado al contexto | **14,002 / 258,941 caracteres (5%)** — el 95% jamás se leyó |
| Entregas | 18 (8 aceptadas, 2 rechazadas por el validador, 9 verificaciones, 2 erratas, 1 oro) |
| Rechazos del validador a la IA | 2 — cita A.19 desplazada una línea; verbatim L.3 cortado por marcador `**` |
| Erratas aplicadas contra evidencia nueva | 4 (A.8, A.11, A.17, C.10) — con bitácora, sin borrar el error |
| Puerta final | ABIERTA (integridad, diferencial, oro, SSOT, narrativos) |

## Hallazgos del piloto (lecciones concretas)

1. **El validador de citas atrapó 2 errores reales de la IA** (línea desplazada por
   línea en blanco no contada; cita cortada por marcador Markdown). Ambos son
   exactamente la clase de error que un humano cometería leyendo rápido — y que
   el mecanismo elimina.
2. **Las erratas son inevitables y sanas si hay mecanismo.** El cierre de la ley
   (entregado en T05) contenía datos que T02 había declarado "no consta"
   (fecha y Diario Oficial de publicación, firmas) y una inexequibilidad que T05
   había declarado ausente (C-150 de 2003, en T07). El comando `corregir` las
   resolvió con evidencia y bitácora: **el piloto no borra errores, los corrige
   con comprobante.**
3. **5% de lectura bastó** para cubrir las fases 0-2 y 8, porque cada fase recibió
   solo los fragmentos pertinentes (lineal para estructura, dirigida para
   temáticas). La arquitectura escala a normas de cualquier tamaño: el costo
   depende de las fases objetivo, no del peso del archivo.
4. **El `solo_verificacion` con cobertura diferida** (corregido en caliente tras
   el atasco de T02) evita re-enviar respuestas completas por cada fragmento:
   presupuesto real, no teatral.
5. El fragmento nunca necesitó más de ~7.5k tokens; la conversación completa del
   piloto es compactable y reanudable desde `run-state.json` sin pérdida.

## Lo que el piloto NO demostró (honestidad de alcance)

- Fases 3-7 y 9 no se ejecutaron (vertical deliberada). La ficha no está completa:
  106/268 campos. Completarla es trabajo de producción, no de piloto.
- La "lectora" fui yo en esta misma sesión; el conector M6 puro (llamada HTTP a la
  API desde Python, con presupuestos/tiempos de la herida Hermes/OpenClaw) queda
  como intercambio aislado detrás de la misma interfaz `next`/`submit`.
- El juicio semántico de las 16 respuestas citadas contra el oro (¿mi respuesta
  dice lo mismo que el esperado?) queda para el humano — el piloto entrega la
  tabla de comparación lista.
- Un solo rechazo de validación por fase de fragmentos fue suficiente en la
  práctica; la política de reintentos con cota se ejercitará con el conector API.

## Estado del backlog M1–M6

- ✅ M1 evidencia obligatoria (ADR-0004) · M2/M3 (ADR-0003) · M4 índice (ADR-0002)
- ✅ M5 set de oro (ADR-0005) · **M6 piloto con IA real (este ADR)** — conector
  API puro pendiente como intercambio aislado

## Decisiones del humano pendientes

1. **~~Aceptación del piloto~~** — **ACEPTADA 2026-09-23** (certificado
   `sistema/piloto/certificado.json`, campo `aceptacion_humana`), incluidas las
   16 respuestas citadas del oro por decisión expresa, con la tabla de
   comparación disponible para revisión puntual.
2. **Juicio semántico de las 16 respuestas citadas** — cubierto por la aceptación
   anterior (revisión puntual siempre posible en `puntaje-oro.json`).
3. **`git init`** — **HECHO 2026-09-23** (6 commits, historia en orden de
   construcción; `.gitattributes` preserva los bytes del corpus).
4. **Ampliación a ficha completa** (fases 3-7, 9) como primera corrida de
   producción — propuesta siguiente a esta aceptación.
