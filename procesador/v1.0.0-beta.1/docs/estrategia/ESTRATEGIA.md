# PATRON ESTRATEGICO — Normativa-Procesador (NP)
# Version: 1.0.0-beta.1 | Fecha: 2026-08-23T23:55:00-05:00

================================================================================
1.  PROPOSITO
================================================================================

Este documento define la estrategia sistematica para procesar una norma
juridica mediante lectura manual. Establece fases, secuencia, criterios de
decision, reglas de activacion y entregables. Es el manual de operaciones del
proyecto NP.

Version actual: 1.0.0-beta.1 (268 elementos, 13 categorias A-M, 10 fases).

================================================================================
2.  PRINCIPIOS RECTORES
================================================================================

P1  PRECISION ABSOLUTA  →  No se afirma lo que no se puede demostrar con el
                            texto normativo.
P2  NO ASUMIR           →  No se completa informacion sin advertir al usuario.
P3  JERARQUIA PRIMERO   →  Se verifica validez formal antes de analizar
                            contenido.
P4  VIGENCIA != EFICACIA → Se distingue siempre entre existencia de la norma,
                            produccion de efectos y aplicabilidad concreta.
P5  TRAZABILIDAD        →  Cada elemento identificado debe poder rastrearse
                            a un articulo, numeral o disposicion especifica.
P6  CONTEXTUALIZACION   →  La norma se lee en relacion con el ordenamiento,
                            no de forma aislada.
P7  SSOT                →  La fuente unica de verdad es data/elementos.json.
                            Los artefactos se derivan via generador.py.

================================================================================
3.  FASES DEL PROCESO DE LECTURA
================================================================================

+-----------------------------------------------------------------------------+
|  FASE 0    PREPARACION                                                      |
|  Duracion: 5-10% del tiempo total                                           |
+-----------------------------------------------------------------------------+

3.1  OBJETIVO: Reunir todo lo necesario antes de tocar el texto normativo.

3.2  ACTIVIDADES:
  [ ] Definir el proposito del analisis (G.4).
  [ ] Identificar la norma objetivo (A.1, A.2, A.3).
  [ ] Verificar disponibilidad del texto (A.18, A.25).
  [ ] Confirmar version a analizar (E.1, E.2).
  [ ] Revisar si existe historial de modificaciones (E.3).
  [ ] Consultar paquete normativo si aplica (D.25).
  [ ] Preparar plantilla de ficha (output/ficha-norma.md).

3.3  DECISION DE CONTINUIDAD:
  [ ] La norma existe y es accesible  →  CONTINUAR a Fase 1
  [ ] La norma no existe o no es accesible  →  ABANDONAR

+-----------------------------------------------------------------------------+
|  FASE 1    IDENTIFICACION FORMAL                                            |
|  Categorias: A (27) + B (22) + I (6) = 55 elementos                         |
|  Duracion: 10-15% del tiempo total                                          |
+-----------------------------------------------------------------------------+

3.4  OBJETIVO: Extraer metadatos de identidad, estructura y validez formal.

3.5  ACTIVIDADES:
  [ ] Extraer metadatos basicos (A.1-A.25).
  [ ] Determinar caracter de la norma (A.30: general/particular/mixto).
  [ ] Verificar reglas de publicidad de actos (A.31).
  [ ] Mapear estructura formal (B.1-B.19).
  [ ] Identificar anexos tecnicos con contenido matematico (B.20).
  [ ] Catalogar formatos obligatorios (B.21, B.22).
  [ ] Verificar jerarquia normativa y competencia (I.1, I.2).
  [ ] Confirmar procedimiento de formacion (I.3).
  [ ] Detectar vicios formales (I.4).
  [ ] Verificar controles previos y posteriores (I.5, I.6).

3.6  DECISION DE CONTINUIDAD:
  [ ] La norma es valida formalmente  →  CONTINUAR a Fase 2
  [ ] Hay vicios formales graves      →  DOCUMENTAR y CONTINUAR con advertencia
  [ ] La norma es nula o inexistente  →  ABANDONAR

+-----------------------------------------------------------------------------+
|  FASE 2    VIGENCIA Y EFICACIA                                              |
|  Categorias: C (20) + K (10) = 30 elementos                                 |
|  Duracion: 10-15% del tiempo total                                          |
+-----------------------------------------------------------------------------+

3.7  OBJETIVO: Determinar si la norma existe, produce efectos y para quien.

3.8  ACTIVIDADES:
  [ ] Determinar estado de vigencia (C.1-C.20).
  [ ] Verificar eficacia inmediata, diferida, condicionada (K.1-K.3).
  [ ] Detectar efectos retroactivos o ultraactivos (K.4, K.5).
  [ ] Delimitar aplicabilidad personal, material, temporal, territorial
      (K.6-K.9).
  [ ] Verificar inaplicabilidad por inconstitucionalidad (K.10).

3.9  DECISION DE CONTINUIDAD:
  [ ] La norma esta vigente y es eficaz  →  CONTINUAR a Fase 3
  [ ] La norma esta derogada o suspendida →  DOCUMENTAR y evaluar si hay
                                              efectos ultraactivos (K.5)
  [ ] La norma es nula  →  ABANDONAR

+-----------------------------------------------------------------------------+
|  FASE 3    VERSIONES                                                        |
|  Categoria: E (13 elementos)                                                |
|  Duracion: 5-10% del tiempo total                                           |
+-----------------------------------------------------------------------------+

3.10  OBJETIVO: Reconstruir la evolucion textual de la norma.

3.11  ACTIVIDADES:
  [ ] Identificar texto original vs. consolidado (E.1, E.2).
  [ ] Reconstruir historial de modificaciones (E.3).
  [ ] Listar articulos modificados, derogados, adicionados (E.4-E.6).
  [ ] Verificar transitorios vigentes (E.7).
  [ ] Revisar version de formatos asociados (E.13).

3.12  DECISION DE CONTINUIDAD:
  [ ] Version clara y trazable  →  CONTINUAR a Fase 4
  [ ] Version confusa o contradictoria  →  PAUSAR para verificacion

+-----------------------------------------------------------------------------+
|  FASE 4    RELACIONES NORMATIVAS                                            |
|  Categoria: D (24 elementos)                                                |
|  Duracion: 10-15% del tiempo total                                          |
+-----------------------------------------------------------------------------+

3.13  OBJETIVO: Ubicar la norma en el tejido del ordenamiento juridico.

3.14  ACTIVIDADES:
  [ ] Identificar normas que deroga, modifica, complementa (D.1-D.8).
  [ ] Mapear paquete normativo si aplica (D.25).
  [ ] Catalogar conceptos tecnicos y orientaciones (D.25a).
  [ ] Identificar principios y reglas de interpretacion aplicables
      (D.15-D.18).
  [ ] Verificar remisiones externas (D.13, D.14).

3.15  DECISION DE CONTINUIDAD:
  [ ] Relaciones claras y completas  →  CONTINUAR a Fase 5
  [ ] Faltan normas del paquete  →  PAUSAR para completar paquete (D.25)

+-----------------------------------------------------------------------------+
|  FASE 5    ANALISIS OPERATIVO                                               |
|  Categorias: F (68) + M (14) = 82 elementos                                 |
|  Duracion: 30-40% del tiempo total                                          |
+-----------------------------------------------------------------------------+

3.16  OBJETIVO: Extraer el contenido sustantivo y los mecanismos de
      gobernanza de la norma.

3.17  ACTIVIDADES — Nucleo operativo (F.1-F.25):
  [ ] Identificar sujetos (obligados, beneficiarios, facultados) (F.1-F.3).
  [ ] Extraer deberes, prohibiciones, facultades, derechos (F.5-F.8).
  [ ] Mapear procedimientos y requisitos (F.9-F.11).
  [ ] Registrar plazos, periodicidades, umbrales (F.12-F.14).
  [ ] Identificar sanciones y excepciones (F.15, F.16).

3.18  ACTIVIDADES — Formulas y tecnicas (F.30-F.34, F.30a-F.30e):
  [ ] Si hay formulas: extraer variables, procedimiento, casos limite (F.31-F.33).
  [ ] Si hay multiples formulas: construir grafo de dependencias (F.30a).
  [ ] Si hay formulas condicionales: mapear rangos y condiciones (F.30b).
  [ ] Si hay tablas de valores: catalogarlas (F.34).

3.19  ACTIVIDADES — Indicadores y metodologias (F.35-F.36c):
  [ ] Si hay indicadores: extraer metas, umbrales, consecuencias (F.35-F.35c).
  [ ] Si hay metodologias: documentar principios, validacion, aprobacion
      (F.36-F.36c).

3.20  ACTIVIDADES — Infraestructura y regulacion sectorial (F.43, F.58, F.62-F.67):
  [ ] Si aplica: mapear zonas tarifarias (F.43).
  [ ] Si aplica: verificar interconexion (F.58).
  [ ] Si aplica: analizar regulacion asimetrica (F.62).
  [ ] Si aplica: documentar condiciones uniformes (F.63).
  [ ] Si aplica: distinguir tarifas reguladas vs. libres (F.64).
  [ ] Si aplica: catalogar fondos sectoriales (F.67).

3.21  ACTIVIDADES — Gobernanza y seguimiento (M.1-M.14):
  [ ] Si hay comites de seguimiento: documentar composicion y funciones (M.1).
  [ ] Si hay auditorias: registrar tipo, periodicidad, entidad (M.2).
  [ ] Si hay planes de accion: documentar causante y seguimiento (M.3).
  [ ] Si hay mecanismos de participacion: registrar tipo y efecto (M.4).
  [ ] Si hay obligaciones de reporte: catalogar destinatarios y plazos (M.5).
  [ ] Si hay incentivos: documentar condiciones de activacion (M.6).
  [ ] Si hay recursos: mapear plazos e instancias (M.7).
  [ ] Si hay garantias: registrar tipo, monto y emisor (M.8).
  [ ] Si hay medidas cautelares: documentar fundamento y plazo (M.9).
  [ ] Si hay procedimiento sancionatorio: etapas y derechos (M.10).
  [ ] Si hay fiscalizacion: programa, comparendos, inspecciones (M.11).
  [ ] Si hay MASC: tipo, obligatoriedad, efecto (M.12).
  [ ] Si hay entidades de defensa: naturaleza y funciones (M.13).
  [ ] Si hay canales de atencion: horarios, tiempos, escalamiento (M.14).

3.22  DECISION DE CONTINUIDAD:
  [ ] Contenido operativo claro  →  CONTINUAR a Fase 6
  [ ] Detectadas ambiguedades o vacios  →  PAUSAR para consulta (G.9)
  [ ] Contradicciones irresolubles  →  DOCUMENTAR y CONTINUAR con advertencia

+-----------------------------------------------------------------------------+
|  FASE 6    INTERPRETACION                                                   |
|  Categoria: J (10 elementos)                                                |
|  Duracion: 10-15% del tiempo total                                          |
+-----------------------------------------------------------------------------+

3.23  OBJETIVO: Aplicar metodos hermeneuticos para resolver ambiguedades.

3.24  ACTIVIDADES:
  [ ] Aplicar interpretacion literal (J.1).
  [ ] Verificar concordancia sistematica (J.2).
  [ ] Consultar trabajos preparatorios si aplica (J.3).
  [ ] Determinar finalidad y objeto (J.4).
  [ ] Evaluar efectos sociales (J.5).
  [ ] Aplicar interpretacion conforme si hay conflicto con norma superior
      (J.8).
  [ ] Documentar argumentos a contrario sensu (J.9).
  [ ] Identificar normas supletorias por vacio (J.10).

3.25  DECISION DE CONTINUIDAD:
  [ ] Interpretacion resuelta  →  CONTINUAR a Fase 7
  [ ] Conflicto de interpretacion persistente  →  DOCUMENTAR en G.7 y
                                                  CONTINUAR con advertencia

+-----------------------------------------------------------------------------+
|  FASE 7    ELEMENTOS ESPECIALES                                             |
|  Categoria: H (12 elementos)                                                |
|  Duracion: 5-10% del tiempo total                                           |
+-----------------------------------------------------------------------------+

3.26  OBJETIVO: Detectar disposiciones atipicas o de alto impacto.

3.27  ACTIVIDADES:
  [ ] Verificar plazo de duracion o sunset clause (H.1, L.15).
  [ ] Confirmar recursos asignados (H.3).
  [ ] Verificar quorum especial o procedimiento de reforma (H.9, H.10).
  [ ] Detectar mecanismos de solucion de controversias (H.8).
  [ ] Verificar control de constitucionalidad (H.11).

3.28  DECISION DE CONTINUIDAD:
  [ ] Sin elementos especiales criticos  →  CONTINUAR a Fase 8
  [ ] Elementos especiales detectados  →  DOCUMENTAR y CONTINUAR

+-----------------------------------------------------------------------------+
|  FASE 8    ANALISIS ECONOMICO / AIR                                         |
|  Categoria: L (20 elementos) — OPCIONAL                                     |
|  Duracion: 10-15% del tiempo total (si aplica)                              |
+-----------------------------------------------------------------------------+

3.29  OBJETIVO: Evaluar eficiencia y costo-beneficio de la norma.

3.30  ACTIVIDADES:
  [ ] Definir problema y objetivos (L.1, L.2).
  [ ] Evaluar costos de cumplimiento (L.4, L.5).
  [ ] Calcular beneficios esperados (L.7).
  [ ] Analizar impacto distributivo, sectorial, ambiental (L.8-L.10).
  [ ] Verificar si existe AIR (L.12).
  [ ] Evaluar carga administrativa (L.17).

3.31  DECISION DE CONTINUIDAD:
  [ ] Analisis economico completo  →  CONTINUAR a Fase 9
  [ ] No aplica analisis economico  →  MARCAR N/A y CONTINUAR a Fase 9

+-----------------------------------------------------------------------------+
|  FASE 9    CIERRE Y METADATOS DEL ANALISIS                                  |
|  Categoria: G (17 elementos)                                                |
|  Duracion: 5-10% del tiempo total                                           |
+-----------------------------------------------------------------------------+

3.32  OBJETIVO: Documentar como se hizo el analisis y cerrar la ficha.

3.33  ACTIVIDADES:
  [ ] Registrar fecha, analista, organizacion (G.1-G.3).
  [ ] Documentar metodologia y nivel de profundidad (G.5, G.6).
  [ ] Registrar conflictos de interpretacion detectados (G.7).
  [ ] Documentar dificultades y consultas realizadas (G.8, G.9).
  [ ] Listar fuentes utilizadas (G.10).
  [ ] Evaluar limitaciones y grado de certeza (G.11, G.12).
  [ ] Formular recomendaciones (G.13).
  [ ] Completar resumen ejecutivo (8 lineas).
  [ ] Calcular puntuacion de calidad (/50).
  [ ] Firmar y archivar.

3.34  DECISION FINAL:
  [ ] Ficha completa y validada  →  ARCHIVAR
  [ ] Ficha incompleta  →  MARCAR como "en_progreso" y programar revision

================================================================================
4.  REGLAS DE DECISION (R1-R15)
================================================================================

Reglas que activan automaticamente otras fases o elementos:

R1  Si en Fase 1 se detecta vicio formal grave (I.4)  →  Documentar en G.8,
    evaluar si afecta validez (I.1-I.3), continuar con advertencia.

R2  Si en Fase 2 la norma esta derogada (C.3)  →  Verificar efectos
    ultraactivos (K.5, C.20) antes de abandonar.

R3  Si en Fase 3 hay versiones intermedias no consolidadas (E.10)  →
    PAUSAR hasta obtener texto consolidado (E.2).

R4  Si en Fase 4 se detecta paquete normativo (D.25)  →  Verificar que
    todas las normas del paquete estan disponibles antes de continuar.

R5  Si en Fase 5 se detecta formula de calculo (F.30)  →  Verificar
    obligatoriamente F.31 (variables), F.32 (procedimiento), F.33 (casos
    limite). Si hay valores indexados, activar F.34 (tablas).

R6  Si en Fase 5 se detecta indicador (F.35)  →  Verificar F.35a (metas
    escalonadas), F.35b (compuestos), F.35c (consecuencias).

R7  Si en Fase 5 se detecta metodologia (F.36)  →  Verificar F.36a
    (principios), F.36b (validacion), F.36c (aprobacion).

R8  Si en Fase 5 se detecta medida cautelar (M.9)  →  Verificar
    efectos sobre terceros y urgencia.
    [NUEVO — Arquetipo SSPD]

R9  Si en Fase 5 se detecta procedimiento sancionatorio (M.10)  →
    Verificar derechos del investigado y cadena de custodia.
    [NUEVO — Arquetipo SSPD]

R10 Si en Fase 5 se detecta regulacion asimetrica (F.62)  →  Verificar
    F.58 (interconexion), F.64 (tarifas reguladas/libres), F.63
    (condiciones uniformes).
    [NUEVO — Arquetipo SSPD]

R11 Si en Fase 5 se detecta obligacion de reporte (M.5)  →
    Diferenciar entre informacion al publico y al regulador (F.65).
    [NUEVO — Arquetipo SSPD]

R12 Si en Fase 1 la norma es de caracter particular (A.30)  →  Verificar
    A.31 (publicidad de actos), M.7 (recursos especificos), y que la
    notificacion fue personal.
    [NUEVO — Arquetipo SSPD]

R13 Si en Fase 5 se detecta fondo sectorial (F.67)  →  Verificar F.42
    (subsidios) y F.42a (financiacion) para coherencia del sistema de
    equidad.
    [NUEVO — Arquetipo SSPD]

R14 Si en Fase 5 se detecta derecho del usuario (M.13)  →
    Verificar M.14 (calidad de atencion) y M.12 (MASC).
    [NUEVO — Arquetipo SSPD]

R15 Si en cualquier fase se detecta norma con anexos tecnicos (B.20)  →
    Verificar F.30-F.34 (formulas), F.44 (estandares), F.45 (modelos).
    [NUEVO — Arquetipo CRA]

================================================================================
5.  FLUJO SSOT (SINGLE SOURCE OF TRUTH)
================================================================================

5.1  Como se integra el generador en el flujo de lectura
--------------------------------------------------------

El analista NO edita la ficha manualmente campo por campo. El flujo es:

  Paso 1: El analista lee la norma y toma notas en borrador.
  Paso 2: El analista transcribe sus hallazgos a la ficha generada
          (output/ficha-norma.md).
  Paso 3: El analista marca elementos como N/A cuando no aplican.
  Paso 4: El analista completa el resumen ejecutivo y el checklist.
  Paso 5: Si durante la lectura detecta un elemento que NO esta en la ficha,
          NO lo agrega a mano. Reporta como gap para actualizar
          data/elementos.json y regenerar.

5.2  Ciclo de mejora continua
-----------------------------

  Auditoria de campo  →  Actualizar elementos.json  →  regenerador.py --all
                                                              ↓
  Nueva ficha validada  ←  Aplicar a norma real  ←  output/ficha-norma.md

5.3  Validacion automatica del sistema
---------------------------------------

El generador incluye 14 reglas de validacion automatica (E001-E013 + W001-W002)
que verifican la integridad de la fuente unica (data/elementos.json) antes de
generar artefactos:

| Codigo | Tipo | Descripcion |
|--------|------|-------------|
| E001 | ERROR | IDs duplicados |
| E002 | ERROR | Campos obligatorios faltantes |
| E003 | ERROR | Dependencias rotas |
| E004 | ERROR | Categorias invalidas (no A-M) |
| E005 | ERROR | Fases invalidas (no 0-9) |
| E006 | ERROR | Estados invalidos |
| E007 | ERROR | Origenes invalidos |
| E008 | ERROR | Tipos de campo invalidos |
| E009 | ERROR | Formato de ID invalido |
| E010 | ERROR | Nombre vacio |
| E011 | ERROR | meta.version obligatorio |
| E012 | ERROR | meta.fecha obligatorio |
| E013 | ERROR | Coherencia de fase padre-hijo |
| W001 | WARNING | Descripcion vacia |
| W002 | WARNING | Atributos derivados en meta |

Si --validate reporta errores, NO se generan artefactos. El analista debe
corregir la fuente y reintentar.

================================================================================
6.  INDICADORES DE CALIDAD DEL ANALISIS
================================================================================

| Criterio | Peso | Como se mide |
|----------|------|--------------|
| Completitud de metadatos (A) | 5 pts | % de A.1-A.31 completos |
| Estructura mapeada (B) | 5 pts | % de B.1-B.22 completos |
| Vigencia verificada (C+K) | 5 pts | Estado C confirmado con fuente |
| Relaciones trazadas (D) | 5 pts | Nro. de relaciones identificadas |
| Versiones documentadas (E) | 5 pts | Historial completo |
| Operativo completo (F+M) | 10 pts | % de F.1-F.67 y M.1-M.14 completos |
| Interpretacion aplicada (J) | 5 pts | Metodo hermeneutico explicitado |
| Metadatos del analisis (G) | 5 pts | G.1-G.17 completos |
| Especiales identificados (H) | 5 pts | H.1-H.12 revisados |
| **TOTAL** | **50 pts** | **>= 40: Excelente / 30-39: Aceptable / < 30: Deficiente** |

================================================================================
7.  ENTREGABLES DEL PROCESO
================================================================================

| # | Entregable | Formato | Ubicacion |
|---|------------|---------|-----------|
| 1 | Ficha de lectura completa | Markdown | output/ficha-norma.md |
| 2 | Resumen ejecutivo (8 lineas) | Texto | Dentro de la ficha |
| 3 | Puntuacion de calidad | Numero /50 | Dentro de la ficha |
| 4 | Lista de gaps detectados | Texto | G.8, G.13 |
| 5 | Recomendaciones | Texto | G.13 |
| 6 | (Opcional) Datos estructurados | JSON | Conforme a output/schema-norma.json |

================================================================================
8.  FUENTES
================================================================================

[Doctrina] Kelsen, Hans — Teoria pura del derecho.
[Doctrina] Atienza, Manuel — Las razones del derecho.
[Doctrina] Garcia de Enterria, Eduardo — La Constitucion como norma.
[Normativa] Constitucion Politica de Colombia.
[Normativa] Ley 1437 de 2011 (Procedimiento Administrativo).
[Normativa] Ley 142 de 1994 (Servicios Publicos Domiciliarios).
[Practica] DNP — Matrices de evaluacion normativa.
[Estándar] ELI (European Legislation Identifier).
[Estándar] LexML Brasil.
