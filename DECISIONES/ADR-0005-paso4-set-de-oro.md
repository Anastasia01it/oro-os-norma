# ADR-0005 — Paso 4: set de oro + la puerta (runner)

- **Fecha:** 2026-09-23
- **Estado:** IMPLEMENTADO (oro verificado 25/25; puerta probada roja y verde)
- **Alcance:** `sistema/oro/`, `sistema/scripts/oro_check.py`, `sistema/scripts/puerta.py`,
  ajuste de salida en el generador NP (`--check-narrativos` ahora sale con código 1
  cuando hay issues: fail-closed).

## Qué se construyó y para qué

**Set de oro** — la regla de medir con respuestas conocidas, construida sobre la
Ley 142 de 1994 (norma propuesta y aceptada como base). 25 casos en tres tipos:

| Tipo | Casos | Qué exige |
|---|---|---|
| `cita` | 16 | respuesta esperada con cita archivo+líneas y texto literal presente |
| `conteo` | 4 | un patrón contado da exactamente el valor declarado (189 artículos numerados, 6 títulos, 15 capítulos, 48 líneas con "parágrafo") |
| `ausente` | 5 | el patrón NO aparece: obliga a decir "no está / no existe" |

Los negativos incluyen: tema ausente en la norma (inteligencia artificial, notarías),
artículo inexistente (999), norma ausente del corpus (Ley 2236 de 2022) y término
ausente en todo el corpus (metaverso).

**Verificador del oro** — `oro_check.py`: antes de medir, demuestra que la regla es
verdad. Comprueba estructura de casos, resolución de citas (con normalización de
espacios: las citas reales cruzan renglones cortados), conteos exactos y ausencias
reales, todo contra el índice validado del paso 1.

**La puerta** — `puerta.py`: ejecuta la cadena completa en orden
(integridad → diferencial → oro → fuente NP → narrativos NP) y se detiene en el
primer fallo. Convierte "despliegue condicionado a 100% en oro" en un comando.

## Evidencia de las pruebas (rojo→verde)

1. Primera corrida del oro: **4 casos falsos detectados en mi propio set** — cita
   desplazada una línea (había una línea en blanco que no conté), cita cruzando un
   salto de línea, conteo de artículos que ignoraba los dos "ARTÍCULO NUEVO" sin
   numerar, y conteo sensible a mayúsculas. Corregidos con honestidad (el valor 191
   pasó a 189 numerados + aclaración; el conteo de párrafos pasó a insensible a caso).
2. Oro final: **25/25 verdadero** (exit 0).
3. Puerta verde: cadena completa `PUERTA ABIERTA` (exit 0).
4. Puerta roja: caso de oro adulterado → `PUERTA CERRADA en 'oro'` (exit 1),
   restaurado y vuelto a verde. Fail-closed probado en ambos sentidos.

## Decisiones y lecciones registradas

- **El oro se audita a sí mismo antes de auditar.** Un caso de oro falso es fallo
  del set, no de quien se evalúa; se corrige el oro o el corpus, nunca se ignora.
- Los conteos del oro deben declarar su semántica exacta ("numerados", "sin
  distinguir mayúsculas"): un número sin semántica es ambiguo y ambigüedad = oro falso.
- `--check-narrativos` del generador NP reportaba issues pero salía con código 0;
  ahora sale 1 (fail-closed) — sin eso, la puerta era decorativa para esa etapa.
- **Aceptación humana pendiente** (registrado en `sistema/oro/README.md`): la verdad
  mecánica del oro está demostrada, pero su aceptación como estándar de medida es
  decisión del humano (revisar los 25 casos).

## Cobertura del plan

- Cubierto: gold set (trampas, vacíos —los negativos—, cálculos —los conteos—),
  runner ordenado. CI pendiente de `git init` (decisión del humano, ya registrada).
- Métrica del plan: casillas §5 = 4 de 5 hechas (falta `parametros.yml`, decisión
  humana). M5 (gold) queda cubierto con este ADR.

## Riesgo aceptado por escrito

- El oro v1 cubre una sola norma (Ley 142) y 25 casos; la generalización a más
  normas llega cuando el piloto lo justifique (cada norma nueva aporta sus casos
  con la misma disciplina rojo→verde).
- Casos de juicio interpretativo (p. ej. "¿qué criterio prima?") todavía no tienen
  representación en el oro: sus respuestas no son cotejables mecánicamente sin
  más diseño (los de cita son los más cercanos). Disparador registrado.
