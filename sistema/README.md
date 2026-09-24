# sistema/ — Infraestructura determinística del procesador de normas

Nada en esta carpeta usa LLM. Todo es script verificable, alineado con
`plan-estructural/SOLUCION-PLAN-ESTRUCTURAL.md` (regla 25: lo determinístico va a script).

## Qué hay

| Ruta | Qué es |
|---|---|
| `scripts/build_manifest.py` | Genera `normas_procesar/manifest.json`: SHA-256 por archivo + `set_hash` del conjunto |
| `scripts/build_index.py` | Construye `data/corpus.index.sqlite` (SQLite FTS5). Aborta si el corpus diverge del manifiesto. Auto-verifica cobertura y reconstrucción lossless |
| `scripts/integrity_check.py` | Control anti-alteración (plan ítem 29): compara corpus actual vs manifiesto. Exit 1 si hay agregados/eliminados/modificados |
| `scripts/differential_check.py` | Control de calidad del índice (plan ítem 21): cobertura triple, reconstrucción lossless, igualdad FTS5 vs fuerza bruta, inclusión vs ripgrep |
| `scripts/corpus_config.py` / `corpus_verify.py` | Compartidos: rutas, hashes, verificadores |
| `data/corpus.index.sqlite` | Índice FTS5 (90 docs, 1811 chunks). Se reconstruye con `build_index.py` |

## Uso

```bash
cd sistema/scripts
python3 build_manifest.py       # tras agregar/quitar/modificar normas del corpus
python3 build_index.py          # reconstruye el índice (re-verifica contra manifiesto)
python3 differential_check.py   # auditoría del índice (exit 0 = índice sano)
python3 integrity_check.py      # sello de integridad (exit 0 = corpus íntegro)
```

Regla operativa: **ninguna corrida sensible (piloto, lotes) sin `integrity_check.py` en verde.**

## Garantías demostradas (2026-09-23, 90 archivos / 1.811 chunks)

- Reconstrucción lossless: 0 fallos (SHA-256 por archivo desde chunks).
- Cobertura: índice == disco == manifiesto.
- FTS5 == tokenizador de referencia (fuerza bruta): 30/30 triples (100%).
- FTS5 ⊆ ripgrep (triple ASCII): 15/15 (100%).

Hallazgos de diseño registrados en `DECISIONES/ADR-0002-paso1-corpus.md`
(incluida la limitación de rg multilínea `-U` y el contrato semántico de cada chequeo).

## Decisiones

- Corpus = `normas_procesar/*.md` (el usuario movió las normas ahí; verificado: 90 archivos, ~21 MB).
- Manifiesto **dentro** de `normas_procesar/` (el sello viaja con la caja).
- Solo stdlib Python: cero dependencias, cero venv (la métrica S lo premia).
- Segmentación por encabezados Markdown; texto almacenado íntegro (el índice es también respaldo verificable).
