# BACKLOG — Normativa-Procesador (NP)
# Version: 1.0.0-beta.1 | Fecha: 2026-09-23T00:00:00-05:00
# Patron activo: SSOT + Generador Derivado

================================================================================
1.  ESTADO ACTUAL DEL SISTEMA
================================================================================

| Metrica | Valor |
|---------|-------|
| Elementos totales | 268 |
| Categorias | 13 (A-M) |
| Fases de lectura | 10 (0-9) |
| Arquetipos de campo auditados | 2 (CRA, SSPD) |
| Observaciones de campo | 40 |
| Elementos nuevos validados | 61 |
| Patron arquitectonico | SSOT + Generador Derivado |

================================================================================
2.  TAREAS COMPLETADAS
================================================================================

| # | Tarea | Fecha |
|---|-------|-------|
| 1 | Estructura arquitectonica del proyecto | 2026-08-23 |
| 2 | Patron handoff (HANDOFF.md) | 2026-08-23 |
| 3 | Patron estrategico (ESTRATEGIA.md) v1 | 2026-08-23 |
| 4 | Categorias A-L originales con descripciones | 2026-08-23 |
| 5 | Modulo md_builder.py con validacion | 2026-08-23 |
| 6 | Plantilla ficha-norma.md (v1, 202 campos) | 2026-08-23 |
| 7 | Matriz de interdependencia (v1) | 2026-08-23 |
| 8 | Esquema JSON (schema-norma.json, v1) | 2026-08-23 |
| 9 | Modelo relacional con DDL PostgreSQL (v1) | 2026-08-23 |
| 10 | Validacion ELI/LexML cruzada | 2026-08-23 |
| 11 | Glosario juridico (v1) | 2026-08-23 |
| 12 | Auditoria de campo 1 — Arquetipo CRA (20 obs, 44 elem propuestos) | 2026-08-23 |
| 13 | Auditoria de campo 2 — Arquetipo SSPD (20 obs, 31 elem propuestos) | 2026-08-23 |
| 14 | Validacion y consolidacion de 61 elementos nuevos | 2026-08-23 |
| 15 | Reorganizacion Categoria F + creacion Categoria M | 2026-08-23 |
| 16 | Regeneracion manual A, B, D, E, F, M con elementos validados | 2026-08-23 |
| 17 | Definicion patron SSOT + Generador Derivado | 2026-08-23 |
| 18 | Construccion data/elementos.json (263 elementos) | 2026-08-23 |
| 19 | Construccion scripts/generador.py (6 generadores) | 2026-08-23 |
| 20 | Ejecucion generador — 6 artefactos derivados | 2026-08-23 |
| 21 | Actualizacion HANDOFF.md y README.md | 2026-08-23 |
| 22 | Actualizacion ESTRATEGIA.md (v2, 10 fases, R1-R15, flujo SSOT) | 2026-08-23 |

================================================================================
3.  TAREAS PENDIENTES — BACKLOG ACTIVO
================================================================================

--------------------------------------------------------------------------------
ALTA PRIORIDAD
--------------------------------------------------------------------------------

| # | Tarea | Descripcion |
|---|-------|-------------|
| P1 | Validar salida del generador | Verificar que ficha-norma.md, schema, SQL, matriz son correctos |
| P2 | Prueba de campo con norma real | Aplicar ficha a una norma colombiana concreta |
| P3 | Cierre v1.0.0-alpha.2 | Tag, release notes, documentacion final |

--------------------------------------------------------------------------------
MEDIA PRIORIDAD
--------------------------------------------------------------------------------

| # | Tarea | Descripcion |
|---|-------|-------------|
| M1 | Auditoria de campo 3 — Arquetipo ANLA | Norma ambiental (licencias, compensaciones, PMA) |
| M2 | Auditoria de campo 4 — Arquetipo INVIMA | Norma sanitaria (registros, buenas practicas) |
| M3 | Auditoria de campo 5 — Arquetipo Superfinanciera | Norma financiera (solvencia, provisiones) |
| M4 | Auditoria de campo 6 — Arquetipo MinTIC | Norma telecomunicaciones (espectro, neutralidad) |
| M5 | Cerrar gaps ELI/LexML | 16 gaps ELI + 5 gaps LexML |
| M6 | Script de migracion de datos | Migrar fichas existentes si cambia esquema |

--------------------------------------------------------------------------------
BAJA PRIORIDAD / BACKLOG FUTURO
--------------------------------------------------------------------------------

| # | Tarea | Descripcion |
|---|-------|-------------|
| L1 | Soporte normas digitales / smart contracts | Elementos para regulacion basada en codigo ejecutable |
| L2 | Soporte common law | Precedentes, case law, stare decisis |
| L3 | Soporte derecho internacional publico | Tratados, convenios, protocolos, reservas |
| L4 | Motor de inferencia normativa | Sistema automatizado de aplicacion de matriz |
| L5 | API REST del esquema JSON | Endpoints CRUD para fichas normativas |
| L6 | Interfaz web de la ficha | Formulario HTML que implemente la plantilla |
| L7 | Exportador a ELI/LexML | Transformar ficha NP a estandar internacional |
| L8 | Validador automatico de normas | Verificar cumplimiento de estandares minimos |

================================================================================
4.  REGISTRO DE DECISIONES ARQUITECTONICAS
================================================================================

[x] Aprobado: 61 elementos nuevos (consolidados desde 81 propuestos originales)
[x] Aprobado: Escision de Categoria M (Mecanismos de Gobernanza y Seguimiento)
[x] Aprobado: Patron SSOT (Single Source of Truth) + Generador Derivado
[x] Aprobado: data/elementos.json como fuente unica
[x] Aprobado: scripts/generador.py como motor de derivacion
[x] Aprobado: output/ como directorio de artefactos generados
[x] Aprobado: Actualizacion ESTRATEGIA.md con 10 fases, R1-R15, flujo SSOT
[ ] Pendiente: Validar con norma real
[ ] Pendiente: Cierre v1.0.0-alpha.2
