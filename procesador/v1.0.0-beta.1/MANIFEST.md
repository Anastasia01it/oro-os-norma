# MANIFEST — Normativa-Procesador v1.0.0-beta.1

## Informacion del paquete

| Campo | Valor |
|-------|-------|
| Nombre | normativa-procesador |
| Version | 1.0.0-beta.1 |
| Fecha de empaquetado | 2026-08-24 |
| Tipo | Version humana-pura (sin conector AI) |
| Estado | Cerrado, listo para produccion |
| Gaps | 0 |
| Elementos | 268 |
| Categorias | 13 (A-M) |
| Fases | 10 (0-9) |
| Reglas de validacion | 14 (E001-E013 + W001-W002) |

## Estructura del paquete

```
v1.0.0-beta.1/
├── data/
│   ├── elementos.json              ← FUENTE UNICA DE VERDAD (268 elementos)
│   └── schema-elementos.json       ← Schema JSON Schema draft-07 para validacion
├── scripts/
│   ├── generador.py                ← Motor de derivacion SSOT
│   │   ├── --validate              ← 14 checks de integridad
│   │   ├── --dry-run               ← Previsualizacion sin escritura
│   │   ├── --check-narrativos      ← Verificacion de documentos manuales (N001-N003)
│   │   └── --all                   ← Genera 6 artefactos
│   └── validar-ficha.py            ← Validador de fichas diligenciadas (M1:
│                                     evidencia obligatoria, citas resolubles
│                                     contra el indice FTS5 del corpus)
├── pruebas-m1/
│   ├── ficha-valida.json           ← Ejemplo aceptable (evidencia real)
│   └── ficha-invalida.json         ← Ejemplo rechazado (citas sin sustento)
├── output/
│   ├── categorias/                 ← 13 archivos .md (A-M)
│   ├── schema-norma.json           ← 268 definiciones de campos
│   ├── modelo-relacional.sql       ← DDL PostgreSQL (16 tablas)
│   ├── ficha-norma.md              ← 268 checkboxes en 10 fases
│   ├── matriz-interdependencia.md  ← 6 reglas de propagacion
│   └── glosario-derivado.md        ← 27 terminos
├── docs/
│   ├── estrategia/
│   │   └── ESTRATEGIA.md           ← Reglas de decision R1-R15
│   └── handoff/
│       └── HANDOFF.md              ← Protocolo de recuperacion
├── templates/
│   └── validacion-eli-lexml.md     ← Plantilla ELI/LexML
├── README.md                       ← Documentacion de entrada
├── BACKLOG.md                      ← Tareas pendientes y futuras
├── CIERRE-DEFINITIVO-v1.0.0-beta.1.md  ← Certificado de cierre
└── MANIFEST.md                     ← Este documento
```

## Instrucciones de uso

### 1. Validar la fuente

```bash
python scripts/generador.py --validate
```

Debe reportar: Errores: 0, Warnings: 0.

### 2. Generar todos los artefactos

```bash
python scripts/generador.py --all
```

Genera/actualiza los 6 artefactos en output/.

### 3. Verificar documentos manuales

```bash
python scripts/generador.py --check-narrativos
```

Debe reportar: Issues: 0.

### 4. Usar la ficha

Abrir output/ficha-norma.md, leer la norma, y marcar los 268 checkboxes.

## Flujo de trabajo SSOT

```
Auditoria de campo detecta cambios
        |
        v
Actualizar data/elementos.json (unico cambio manual)
        |
        v
python scripts/generador.py --validate
        |
        v
python scripts/generador.py --all
        |
        v
python scripts/generador.py --check-narrativos
        |
        v
Actualizar manualmente (si es necesario): docs/estrategia/ESTRATEGIA.md, docs/handoff/HANDOFF.md
```

## Requisitos

- Python 3.8+
- Sin dependencias externas (solo libreria estandar)

## Versiones futuras

- v2.0: Conector AI (ai_connector.py) para lectura automatica de normas

## Licencia

Proyecto interno. Uso restringido al equipo de analisis normativo.

---
Empaquetado: 2026-08-24
Firma: Kimi (Asistente de Auditoria de Verdad)
