# Normativa-Procesador (NP)

Sistema integral para la lectura manual, analisis estructurado y gestion de
normas juridicas. Disenado para escalabilidad ilimitada mediante el patron
Single Source of Truth (SSOT) + Generacion Derivada.

## Estado actual

| Metrica | Valor |
|---------|-------|
| Version | 1.0.0-beta.1 |
| Elementos | 268 |
| Categorias | 13 (A-M) |
| Fases de lectura | 10 (0-9) |
| Arquetipos auditados | 2 (CRA, SSPD) |

## Arquitectura SSOT

```
data/elementos.json  →  scripts/generador.py  →  6 artefactos
                              ↓
                    [categorias, schema, sql, ficha, matriz, glosario]
```

**Para regenerar todos los artefactos:**
```bash
python scripts/generador.py --all
```

## Categorias

| Categoria | Elementos | Descripcion |
|-----------|-----------|-------------|
| A | 27 | Metadatos de identificacion |
| B | 22 | Estructura formal interna |
| C | 20 | Estados de vigencia |
| D | 24 | Relaciones normativas |
| E | 13 | Control de versiones |
| F | 68 | Analisis operativo (tecnico) |
| G | 17 | Metadatos del analisis |
| H | 12 | Elementos especiales |
| I | 6 | Jerarquia y validez formal |
| J | 10 | Interpretacion y aplicacion |
| K | 10 | Eficacia y aplicabilidad |
| L | 20 | Analisis economico / AIR |
| M | 14 | Mecanismos de gobernanza y seguimiento |

## Documentacion clave

- `docs/handoff/HANDOFF.md` — Recuperacion de contexto
- `docs/estrategia/ESTRATEGIA.md` — Flujo de lectura (10 fases)
- `docs/auditoria-campo/` — Auditorias de arquetipos CRA y SSPD
- `BACKLOG.md` — Tareas pendientes

## Convenciones

- **Versionado:** SemVer
- **Fechas:** ISO 8601, zona -05:00 (Bogota)
- **IDs:** NP-[CAT]-[NUM]
- **Foco:** Derecho civil latinoamericano, referencia Colombia
- **Escritura:** open() nativo de Python (nunca write_file para >5000 chars)
