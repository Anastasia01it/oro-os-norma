# HANDOFF — Normativa-Procesador (NP)
# Version: 1.0.0-beta.1 | Fecha: 2026-08-23T23:45:00-05:00

================================================================================
1.  SNAPSHOT DE CONTEXTO
================================================================================

Proyecto: Normativa-Procesador (NP)
Version: 1.0.0-alpha.2
Total elementos: 268 en 13 categorias (A-M)
Fases de lectura: 10 (0-9)
Arquetipos auditados: 2 (CRA, SSPD)
Observaciones de campo: 40
Elementos nuevos validados: 61

Patron arquitectonico activo: SSOT (Single Source of Truth) + Generador Derivado
Fuente unica: data/elementos.json
Motor de derivacion: scripts/generador.py
Artefactos generados: output/ (categorias, schema, sql, ficha, matriz, glosario)

================================================================================
2.  ESTRUCTURA DEL PROYECTO
================================================================================

normativa-procesador/
├── data/
│   └── elementos.json              ← FUENTE UNICA (268 elementos)
├── scripts/
│   ├── md_builder.py               ← Constructor Markdown con validacion
│   └── generador.py                ← Motor de derivacion (6 artefactos)
├── docs/
│   ├── handoff/
│   │   └── HANDOFF.md              ← Este archivo
│   ├── estrategia/
│   │   └── ESTRATEGIA.md           ← 10 fases + 15 reglas
│   ├── categorias/                 ← Manuales (A-M, con descripciones)
│   │   ├── A-METADATOS.md
│   │   ├── B-ESTRUCTURA.md
│   │   ├── C-VIGENCIA.md
│   │   ├── D-RELACIONES.md
│   │   ├── E-VERSIONES.md
│   │   ├── F-OPERATIVO.md
│   │   ├── G-METADATOS-ANALISIS.md
│   │   ├── H-ESPECIALES.md
│   │   ├── I-JERARQUIA.md
│   │   ├── J-INTERPRETACION.md
│   │   ├── K-EFICACIA.md
│   │   ├── L-ECONOMICO.md
│   │   └── M-GOBERNANZA.md
│   ├── auditoria-campo/
│   │   ├── OBSERVACIONES-CAMPO.md      ← Arquetipo CRA (20 obs)
│   │   ├── OBSERVACIONES-CAMPO-SSPD.md ← Arquetipo SSPD (20 obs)
│   │   └── ELEMENTOS-VALIDADOS.md      ← Maestro de 268 elementos
│   └── glosario-juridico.md
├── templates/                      ← (obsoleto, usar output/)
├── schemas/                        ← (obsoleto, usar output/)
├── output/                         ← GENERADO AUTOMATICAMENTE
│   ├── categorias/                 ← 13 archivos .md
│   ├── schema-norma.json
│   ├── modelo-relacional.sql
│   ├── ficha-norma.md
│   ├── matriz-interdependencia.md
│   └── glosario-derivado.md
├── README.md
├── BACKLOG.md
└── .gitignore (sugerido: output/)

================================================================================
3.  PROTOCOLO DE RECUPERACION (6 pasos)
================================================================================

Paso 1: Leer este archivo (HANDOFF.md).
Paso 2: Leer data/elementos.json (268 elementos).
Paso 3: Ejecutar `python scripts/generador.py --all`.
Paso 4: Leer docs/estrategia/ESTRATEGIA.md.
Paso 5: Leer docs/auditoria-campo/.
Paso 6: Consultar BACKLOG.md.

================================================================================
4.  REGLA DE ORO DE ESCRITURA
================================================================================

| Documento | Herramienta | Razon |
|-----------|-------------|-------|
| Fichas normativas | md_builder.py | Estructura compleja, validacion |
| Narrativos | open() Python | Texto simple, open() garantiza saltos |
| Derivados | generador.py | Consistencia desde SSOT |
| >5000 chars | NUNCA write_file | Colapsa saltos de linea |

================================================================================
5.  COMO AGREGAR UN NUEVO ELEMENTO
================================================================================

1. Editar data/elementos.json.
2. Ejecutar: python scripts/generador.py --all
3. Verificar output/.
4. Actualizar manualmente: ESTRATEGIA.md (si afecta reglas).
5. Actualizar manualmente: HANDOFF.md (version, conteos).
6. NO editar output/ directamente.

================================================================================
6.  CHANGELOG
================================================================================

2026-08-23  v1.0.0-alpha.1  Creacion, 202 elementos en 12 categorias.
2026-08-23  v1.0.0-alpha.2  Auditoria CRA+SSPD, 268 elementos, 13 categorias,
                            patron SSOT + generador.py, artefactos derivados.
