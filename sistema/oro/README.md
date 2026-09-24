# Set de oro — casos de aceptación con respuesta conocida

**Principio rector:** quien mide debe ser verdad antes de medir. Cada caso de este
directorio tiene una pregunta, una respuesta esperada y —cuando aplica— una cita
verificable contra el corpus. `oro_check.py` comprueba **primero** que esas
respuestas esperadas son ciertas; solo un oro aprobado puede usarse para evaluar
al procesador o a la IA.

## Qué hay

- `casos-oro.json` — los casos (v1: 25, construidos sobre Ley 142 de 1994).
- `../scripts/oro_check.py` — el verificador del oro (no evalúa a nadie; audita al oro).

## Los tres tipos de caso

| verificacion | significado |
|---|---|
| `cita` | la respuesta esperada cita archivo+líneas y el texto citado aparece literalmente ahí |
| `conteo` | un patrón contado sobre el archivo da exactamente el valor declarado |
| `ausente` | el patrón **no** aparece (negativo: la respuesta correcta es "no está / no existe") |

Alcance del `ausente`: `archivo` (en esa norma), `corpus` (en todo el corpus),
`nombres` (en los nombres de archivo).

## Por qué hay negativos

Un sistema que siempre responde algo cae ante la pregunta sin respuesta. Los 5
negativos obligan al procesador a **decir que no sabe** cuando el corpus no
contiene la respuesta, en vez de inventarla.

## Cómo agregar un caso (reglas)

1. La respuesta esperada debe poder comprobarse contra el corpus (cita, conteo o ausencia).
2. Toda cita debe resolverse: archivo presente, líneas dentro del rango, texto presente.
3. Los conteos deben usar patrones robustos (plegado de mayúsculas/acentos; el verificador aplica ambos).
4. Un negativo debe ser negativo de verdad: verificar la ausencia antes de registrar el caso.
5. Rojo→verde obligatorio: el verificador debe poder fallar el caso nuevo antes de aprobarlo.

## Estado de aceptación humana

El oro es la regla con la que se medirá todo lo demás; su verdad mecánica está
demostrada (25/25), pero su **aceptación** como estándar de medida corresponde
al humano (revisión de los casos en `casos-oro.json`). Hasta esa aceptación,
el oro es propuesta técnica verificada, no estándar firmado.

## Relación con el plan

Cubre el ítem "juego de pruebas oro (incluye negativos)" de
`plan-estructural/SOLUCION-PLAN-ESTRUCTURAL.md`. La integración con el piloto
(paso 5) consumirá estos casos: la IA deberá producir respuestas que el oro
confirme, y su ficha deberá pasar `validar-ficha.py` (M1).
