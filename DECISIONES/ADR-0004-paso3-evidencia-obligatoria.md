# ADR-0004 — Paso 3: M1, evidencia obligatoria en el esquema de fichas

- **Fecha:** 2026-09-23
- **Estado:** IMPLEMENTADO (pruebas rojo→verde→regresión superadas)
- **Alcance:** `procesador/v1.0.0-beta.1/` — generador (esquema + plantilla),
  validador nuevo, ejemplos de prueba. La fuente `elementos.json` no se tocó
  (hash `cd28f9451bceeab2` intacto).

## Qué se construyó y para qué

**Propósito en lenguaje natural:** cuando la IA (o un humano) diligencie la ficha
de una norma, cada casilla marcada como hecha debe venir con su comprobante:
qué archivo del corpus la sostiene, en qué línea exacta, y la cita textual.
El sistema valida mecánicamente que esos comprobantes existen y dicen lo que la
ficha afirma. Sin comprobante, la ficha no se acepta.

1. **Esquema de la ficha** (`output/schema-norma.json`, generado):
   - `evidencia` pasa a ser obligatoria (arreglo mínimo 1 elemento); cada cita
     exige: campo de la taxonomía (p. ej. A.1), cita con formato
     `ARCHIVO.md#Ln` o `ARCHIVO.md#Ln-Lm`, tipo (texto/tabla/calculo) y la
     cita textual (`verbatim`).
   - `meta` gana dos campos: `norma_archivo` (el .md analizado) y
     `corpus_set_hash` (el sello del corpus del paso 1): la ficha queda atada
     a la versión exacta del corpus contra la que se produjo.
2. **Plantilla** (`output/ficha-norma.md`): instrucciones de evidencia obligatoria
   y un bloque final con el formato JSON esperado y sus cuatro reglas.
3. **Validador** (`scripts/validar-ficha.py`, solo biblioteca estándar):
   - V1 forma de la ficha; V2 el sello coincide con el manifiesto vigente;
   - V3 todo campo completado tiene evidencia y REF. ARTICULO cuando la
     taxonomía lo exige; además detecta campos declarados bajo la fase
     incorrecta (error encontrado durante las propias pruebas);
   - V4 cada cita referencia un campo real con formato y tipo válidos;
   - V5 cada cita resuelve a líneas reales del corpus —usando el índice del
     paso 1— y el texto citado aparece literalmente en ellas.

## Pruebas (secuencia rojo→verde→regresión)

| Caso | Resultado esperado | Resultado |
|---|---|---|
| `pruebas-m1/ficha-valida.json` (cita real de LEY-142-1994) | ACEPTADA | ✅ exit 0 |
| `pruebas-m1/ficha-invalida.json` (sello falso, cita inventada, archivo inexistente) | RECHAZADA con V2/V5 | ✅ exit 1, 3 problemas |
| Regresión: campo bajo fase incorrecta | RECHAZADA con V3 | ✅ rechazada |
| `--validate` / `--check-narrativos` | sin regresiones | ✅ verde |
| `--all` × 2 + diff (determinismo M3) | idéntico | ✅ preservado |

## Hallazgo durante las pruebas (queda registrado)

La primera versión del validador **no contaba campos completados** cuando el
ejemplo los puso bajo la fase 0, porque A.1 pertenece a la fase 1: el campo
quedaba invisible para el control de cobertura. El validador ahora exige que
cada campo esté bajo la fase que la fuente le asigna. Lección: un control de
cobertura debe verificar tanto la presencia como la ubicación.

## Cobertura del plan con este paso

- **Cubierto:** ítem 16 (evidencia obligatoria y referenciada — el eslabón
  faltante entre ficha y corpus), ítem 21 (el validador consume el índice
  validado del paso 1: la cadena de confianza es corpus ⇄ índice ⇄ ficha).
- **Parcial:** la escritura en `evidencia/registro.jsonl` (kit del plan) llega
  con el piloto (paso 5); M1 deja la ficha verificable, que es su prerrequisito.

## Riesgo aceptado por escrito

- El validador implementa a mano el subconjunto del esquema que usa NP (no
  depende de la biblioteca `jsonschema`: criterio S, superficie de dependencia).
  Si el esquema crece en tipos complejos (anyOf, $ref), toca ampliar el
  validador o reconsiderar la dependencia — disparador registrado.
- `--offline` permite validar sin corpus (solo estructura); quien lo use debe
  saber que una ficha "estructuralmente válida" sin corpus no es verdad todavía.

## Estado del backlog M1–M6

- ✅ M1 (este ADR), M2 (ADR-0003), M3 (ADR-0003), M4 (ADR-0002)
- ⏭ M5 set de oro (paso 4) · M6 conector IA vía dsh (paso 5, piloto Ley 142)
