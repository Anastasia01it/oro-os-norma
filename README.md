# ============================================================
# Norma — procesador de normas Colombianas (ORO-OS)
# ============================================================

Infraestructura verificable para procesar normas legales Colombianas con IA,
sin que una afirmación no comprobable pase por verdad.

## Mapa del repositorio

| Ruta | Qué es | Cómo se obtiene |
|---|---|---|
| `normas_procesar/` | Corpus: 90 normas (.md, ~21 MB) + `manifest.json` (sello SHA-256) | Fuente primaria: verificación externa pendiente (riesgo registrado en ADR-0001) |
| `sistema/scripts/` | Herramientas determinísticas: manifiesto, índice FTS5, integridad, diferencial, oro, puerta, piloto | Trabajo propio |
| `sistema/data/` | Índice SQLite FTS5 (reconstruible; NO versionado) | `python3 sistema/scripts/build_index.py` |
| `sistema/oro/` | Set de oro: casos de aceptación con respuesta conocida | Trabajo propio, verificado contra el corpus |
| `sistema/piloto/` | Piloto M6: ficha de Ley 142, bitácora, certificado | Salida del piloto (ADR-0006) |
| `procesador/v1.0.0-beta.1/` | Normativa-Procesador: taxonomía de 268 campos (SSOT) + generador | Paquete recibido (tarball = original sellado) + mejoras M2/M3/M1 |
| `plan-estructural/` | Plan de 35 fallas de LLM + solución por ítem | Trabajo propio |
| `DECISIONES/` | ADR-0001…0006: memoria de decisiones con evidencia | Trabajo propio |

## Cadena de confianza en un comando

```bash
python3 sistema/scripts/puerta.py
```

`PUERTA ABIERTA` = corpus íntegro, índice fiel al corpus, set de oro verdadero,
fuente del procesador consistente, documentos narrativos sin desfase.

## Reglas de versionado (acordadas)

1. **Lo derivado no se versiona**: el índice SQLite y los artefactos generados
   (`procesador/*/output/`) se reconstruyen con sus scripts — son deterministas
   desde la fuente (ADR-0003, M3).
2. **El sello viaja con el corpus**: `normas_procesar/manifest.json` se versiona
   siempre; cambiar el corpus sin regenerar el manifiesto rompe la puerta.
3. **Nada se corrige sin evidencia**: las erratas al contenido verificado siguen
   el mecanismo del piloto — corrección + comprobante + bitácora (ADR-0006).
4. **Cambios al plan o al procesador requieren ADR** (M2/M3 del plan: el plan es
   la fuente de verdad versionada y solo el humano aprueba cambios).
5. El búfer transitorio `sistema/piloto/respuesta.json` no se versiona: la
   evidencia vive en `registro.jsonl` y `ficha.json`.

## Estado

- Pasos 1–5 completados (ver `DECISIONES/`). Backlog M1–M6 cerrado en versión piloto.
- Pendiente decisión humana: aceptación del piloto, juicio semántico del oro,
  fuente primaria del corpus, `parametros.yml`.
