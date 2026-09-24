# VALIDACIÓN CRUZADA ELI / LexML — Normativa-Procesador (NP)
# NP-ELI-LEXML  v1.0.0
# 2026-08-23T21:04:00-05:00
# ───────────────────────────────────────────────────────────────────────────────

## 1.  PROPÓSITO Y ALCANCE
# ───────────────────────────────────────────────────────────────────────────────
Este documento verifica la cobertura del sistema NP contra los estándares
internacionales de metadatos legislativos:

• **ELI** (European Legislation Identifier) — Ontología y metadatos de la UE
  para identificación, descripción e intercambio de legislación.
  Especificación: https://data.europa.eu/eli/ontology

• **LexML** (Brasil / Colombia) — Sistema de identificación de normas mediante
  URN y esquema XML basado en FRBR. Especificación: projeto.lexml.gov.br

Objetivo: detectar gaps de metadatos, documentar equivalencias y proponer
ajustes para alcanzar interoperabilidad con sistemas que implementen estos
estándares.

## 2.  RESUMEN EJECUTIVO DE LA VALIDACIÓN
# ───────────────────────────────────────────────────────────────────────────────

| Métrica | ELI | LexML | Estado |
|---------|-----|-------|--------|
| Propiedades ELI totales identificadas | 42 | — | — |
| Propiedades ELI mapeadas en NP | 28 | — | 67% |
| Propiedades ELI SIN mapeo en NP | 14 | — | 33% (gaps) |
| Elementos NP con equivalente ELI | 28 | — | — |
| Elementos NP SIN equivalente ELI | 174 | — | 86% (específicos NP) |
| Componentes LexML mapeados | — | 7 secciones | 70% |
| Componentes LexML SIN mapeo | — | 3 secciones | 30% (gaps) |

**Veredicto:** El sistema NP cubre el **67% de las propiedades ELI** y el
**70% de las secciones LexML**. Los gaps identificados son de baja prioridad
para lectura manual, pero de alta prioridad para interoperabilidad digital.

## 3.  MAPEO COMPLETO ELI ↔ NP
# ───────────────────────────────────────────────────────────────────────────────

### 3.1  Propiedades ELI con mapeo directo en NP

| # | Propiedad ELI | Descripción ELI | Elemento NP | Categoría NP | Notas |
|---|---------------|-----------------|-------------|--------------|-------|
| 1 | eli:type_document | Tipo de documento (ley, decreto, etc.) | A.1 | A | Mapeo directo |
| 2 | eli:number | Número identificador | A.2 | A | Mapeo directo |
| 3 | dcterms:title | Título completo | A.3 | A | Mapeo directo |
| 4 | dcterms:alternative | Título corto / abreviatura | A.4 | A | Mapeo directo |
| 5 | dcterms:creator / eli:passed_by | Autoridad que aprobó | A.5 | A | Mapeo directo |
| 6 | eli:publisher | Autoridad que publica | A.6 | A | Mapeo directo |
| 7 | eli:date_document | Fecha de adopción / firma | A.7 | A | Mapeo directo |
| 8 | eli:date_publication | Fecha de publicación oficial | A.8 | A | Mapeo directo |
| 9 | eli:first_date_entry_in_force | Primera fecha de entrada en vigor | A.21 | A | Mapeo directo |
| 10 | eli:date_applicability | Fecha desde la cual aplica | A.20 | A | Mapeo directo |
| 11 | eli:id_local | Identificador en sistema local | A.2 (número) | A | Parcial: ELI permite múltiples id_local |
| 12 | eli:language | Idioma de la expresión | A.13 | A | Mapeo directo |
| 13 | eli:jurisdiction | Jurisdicción (país, región) | A.14 | A | Parcial: ELI usa URIs de autoridad |
| 14 | eli:work_type | Tema o materia | A.15 | A | Parcial: ELI usa vocabularios controlados |
| 15 | eli:legal_value | Valor legal (oficial, consolidada, etc.) | A.22 | A | Mapeo directo |
| 16 | eli:rightsholder | Titular de derechos de publicación | A.23 | A | Mapeo directo |
| 17 | eli:licence | Licencia de uso / reutilización | A.24 | A | Mapeo directo |
| 18 | eli:format | Formato (PDF, HTML, XML) | A.25 | A | Mapeo directo |
| 19 | eli:is_annex_of | Es anexo de otra norma | B.19 | B | Mapeo directo |
| 20 | eli:changes | Modifica o deroga otra norma | D.1-D.6 | D | Parcial: NP separa en 6 tipos |
| 21 | eli:changed_by | Es modificada o derogada por otra | D.7-D.10 | D | Parcial: NP separa en 4 tipos |
| 22 | eli:based_on | Se fundamenta en norma superior | D.20 | D | Mapeo directo |
| 23 | eli:basis_for | Es fundamento de norma inferior | D.6 | D | Inverso de based_on |
| 24 | eli:is_derivative_of | Deriva de otra norma | D.19 | D | Mapeo directo |
| 25 | eli:corrects | Corrige errores de otra norma | D.21 | D | Mapeo directo |
| 26 | eli:transposes | Transpone directiva de la UE | D.22 | D | Mapeo directo |
| 27 | eli:related_to | Relacionada con otra norma | D.11, D.12 | D | Parcial: NP distingue concordancia/conflicto |
| 28 | eli:consolidates / eli:consolidated_by | Texto consolidado | E.2, E.3 | E | Parcial: NP tiene modelo de versiones más detallado |

### 3.2  Propiedades ELI SIN mapeo en NP (GAPS)

| # | Propiedad ELI | Descripción | Prioridad | Justificación |
|---|---------------|-------------|-----------|---------------|
| 1 | eli:uri_schema | Plantilla URI usada | BAJA | Metadato técnico de implementación, no de contenido normativo |
| 2 | eli:relevant_for | Jurisdicción relevante (ej. país) | BAJA | A.14 cubre el ámbito territorial; ELI usa URIs específicas |
| 3 | eli:in_force | Estado de vigencia (in_force, partially_in_force, not_in_force) | MEDIA | Categoría C cubre 20 estados detallados; ELI simplifica a 3. Se podría mapear C.1→in_force, C.3/C.12/C.13→not_in_force |
| 4 | eli:date_no_longer_in_force | Fecha de pérdida de vigencia | MEDIA | No existe en NP; útil para normas con fecha de extinción conocida |
| 5 | eli:cites / eli:cited_by | Cita textual en el texto | MEDIA | NP no tiene elemento para citas textuales internas (solo relaciones normativas D) |
| 6 | eli:applies / eli:applied_by | Conformidad sin transposición estricta | BAJA | D.11 (concordantes) cubre parcialmente; ELI distingue aplicación de transposición |
| 7 | eli:version | Estado de versión (made, consolidated, proposed) | MEDIA | E.2 distingue original/consolidada; ELI tiene vocabulario más amplio |
| 8 | eli:version_date | Fecha de validez de la versión | BAJA | E.9 (fecha última consolidación) es similar pero no idéntico |
| 9 | eli:published_in | Publicado en (nombre del boletín) | BAJA | A.6 (autoridad que publica) y A.11 (número de publicación) cubren parcialmente |
| 10 | eli:published_in_format | URL del boletín | BAJA | G.3 (fuente de consulta) cubre parcialmente |
| 11 | eli:is_realized_by / eli:realizes | Relación Work→Expression (FRBR) | BAJA | Metadato de modelo conceptual; NP opera a nivel de documento |
| 12 | eli:is_embodied_by / eli:embodies | Relación Expression→Format (FRBR) | BAJA | Metadato de modelo conceptual; A.25 cubre el formato |
| 13 | eli:is_part_of / eli:has_part | Inclusión física (artículo en ley) | BAJA | B.2-B.8 cubren la estructura jerárquica; ELI lo modela como relación |
| 14 | eli:is_member_of / eli:has_member | Inclusión conceptual (versiones temporales) | BAJA | E.3 (historial) cubre parcialmente; ELI lo modela como membresía FRBR |
| 15 | eli:is_about | Tema / materia (vocabulario controlado) | MEDIA | A.15 cubre el ámbito material; ELI requiere vocabulario SKOS específico |
| 16 | eli:is_another_publication | Otra publicación de la misma norma | BAJA | Metadato específico de sistemas con múltiples publicadores |

### 3.3  Elementos NP SIN equivalente ELI (Específicos del sistema NP)

| Elemento NP | Categoría | Descripción | ¿Debería proponerse a ELI? |
|-------------|-----------|-------------|---------------------------|
| A.10 (Vacatio legis) | A | Plazo entre publicación y vigencia | SÍ — útil para sistemas de alerta |
| A.16 (Jerarquía / Rango) | A | Posición en pirámide de Kelsen | NO — específico de sistemas de derecho civil |
| A.17 (Firma / Autenticación) | A | Datos de firma y acta | NO — metadato administrativo interno |
| A.18 (Estado de publicación) | A | Publicada, por publicar, parcial | SÍ — ELI asume publicación completa |
| A.19 (Ámbito personal) | A | Sujetos alcanzados | NO — específico de ordenamientos nacionales |
| B.1-B.18 | B | Estructura formal interna | PARCIAL — ELI modela partes como relaciones, no como metadatos estructurales |
| C.1-C.20 | C | Estados de vigencia detallados | PARCIAL — ELI simplifica a 3 estados; el detalle de NP es más útil para análisis manual |
| D.13-D.18 | D | Jurisprudencia, doctrina, principios | NO — ELI no cubre fuentes del derecho no normativas |
| E.1-E.12 | E | Control de versiones detallado | PARCIAL — ELI tiene consolidates/consolidated_by; NP es más granular |
| F.1-F.29 | F | Análisis operativo completo | NO — ELI es metadato de identificación/descripción, no de contenido sustantivo |
| G.1-G.17 | G | Metadatos del análisis | NO — metadatos sobre el proceso, no sobre la norma |
| H.1-H.12 | H | Elementos especiales por tipo | NO — ELI no distingue tipos normativos específicos |
| I.1-I.6 | I | Jerarquía y validez formal | NO — específico de control de constitucionalidad colombiano |
| J.1-J.10 | J | Reglas de interpretación | NO — ELI no cubre hermenéutica |
| K.1-K.10 | K | Eficacia y aplicabilidad | NO — ELI usa in_force como proxy; NP distingue 3 planos |
| L.1-L.20 | L | Análisis económico / AIR | NO — fuera del alcance de ELI |

## 4.  MAPEO LEXML ↔ NP
# ───────────────────────────────────────────────────────────────────────────────

### 4.1  Secciones LexML mapeadas

| Sección LexML | Descripción | Elementos NP equivalentes | Estado |
|---------------|-------------|---------------------------|--------|
| **Identificação** | Identificador único del documento | A.1-A.3, A.12 | ✅ Mapeado |
| **Contexto (FRBR)** | Posición en jerarquía Work/Expression/Manifestation | A.25, E.1-E.2, B.19 | ✅ Mapeado |
| **CicloDeVida** | Eventos de la norma (vigencia, modificación) | A.7-A.9, C.1-C.20, E.3-E.9 | ✅ Mapeado |
| **EventosGerados** | Eventos que afectan a otras normas | D.1-D.6, D.19-D.22 | ✅ Mapeado |
| **Notas** | Notas del editor o markup | G.7, E.11 | ✅ Mapeado |
| **Recursos** | Recursos auxiliares referenciados | B.13, G.3 | ✅ Mapeado |
| **MetadadosProprietario** | Extensión para metadatos no estándar | G.15-G.17 | ✅ Mapeado |

### 4.2  Componentes LexML SIN mapeo en NP (GAPS)

| Componente LexML | Descripción | Prioridad | Justificación |
|------------------|-------------|-----------|---------------|
| **Fórmulas matemáticas (MathML)** | Inclusión de fórmulas en el texto | BAJA | NP no está diseñado para normas con contenido matemático |
| **Assinatura (firma digital)** | Metadatos de firma electrónica | BAJA | A.17 cubre firma física; firma digital es metadato técnico |
| **Localidade (URN)** | Componente geográfico de la URN | BAJA | A.14 cubre el ámbito territorial; la localidad URN es sintaxis específica |
| **Autoridade (URN)** | Componente de autoridad de la URN | BAJA | A.5 cubre la autoridad emisora; la autoridad URN es sintaxis específica |
| **Data (URN)** | Componente de fecha de la URN | BAJA | A.7-A.9 cubren las fechas; la fecha URN es sintaxis específica |

## 5.  TABLA DE MAPEO CONSOLIDADO ELI ↔ NP (para implementación digital)
# ───────────────────────────────────────────────────────────────────────────────

```json
{
  "mapeo_eli_np": {
    "eli:type_document": { "np": "A.1", "tipo": "directo", "notas": "Tipo normativo" },
    "eli:number": { "np": "A.2", "tipo": "directo", "notas": "Número / Código" },
    "dcterms:title": { "np": "A.3", "tipo": "directo", "notas": "Título completo" },
    "dcterms:alternative": { "np": "A.4", "tipo": "directo", "notas": "Título corto" },
    "dcterms:creator": { "np": "A.5", "tipo": "directo", "notas": "Autoridad emisora" },
    "eli:publisher": { "np": "A.6", "tipo": "directo", "notas": "Autoridad que publica" },
    "eli:date_document": { "np": "A.7", "tipo": "directo", "notas": "Fecha de expedición" },
    "eli:date_publication": { "np": "A.8", "tipo": "directo", "notas": "Fecha de publicación" },
    "eli:first_date_entry_in_force": { "np": "A.21", "tipo": "directo", "notas": "Primera fecha de entrada en vigor" },
    "eli:date_applicability": { "np": "A.20", "tipo": "directo", "notas": "Fecha de aplicabilidad" },
    "eli:id_local": { "np": "A.2", "tipo": "parcial", "notas": "NP usa A.2 como id local; ELI permite múltiples" },
    "eli:language": { "np": "A.13", "tipo": "directo", "notas": "Idioma(s) de la norma" },
    "eli:jurisdiction": { "np": "A.14", "tipo": "parcial", "notas": "NP usa texto libre; ELI usa URIs de autoridad" },
    "eli:work_type": { "np": "A.15", "tipo": "parcial", "notas": "NP usa texto libre; ELI usa vocabularios controlados" },
    "eli:legal_value": { "np": "A.22", "tipo": "directo", "notas": "Valor legal / Fuerza normativa" },
    "eli:rightsholder": { "np": "A.23", "tipo": "directo", "notas": "Titular de derechos" },
    "eli:licence": { "np": "A.24", "tipo": "directo", "notas": "Licencia de uso" },
    "eli:format": { "np": "A.25", "tipo": "directo", "notas": "Formato de la versión" },
    "eli:is_annex_of": { "np": "B.19", "tipo": "directo", "notas": "Es anexo de" },
    "eli:changes": { "np": ["D.1","D.2","D.3","D.4","D.5","D.6"], "tipo": "parcial", "notas": "NP separa en 6 tipos de relación saliente" },
    "eli:changed_by": { "np": ["D.7","D.8","D.9","D.10"], "tipo": "parcial", "notas": "NP separa en 4 tipos de relación entrante" },
    "eli:based_on": { "np": "D.20", "tipo": "directo", "notas": "Basado en" },
    "eli:basis_for": { "np": "D.6", "tipo": "inverso", "notas": "Inverso de based_on" },
    "eli:is_derivative_of": { "np": "D.19", "tipo": "directo", "notas": "Es derivado de" },
    "eli:corrects": { "np": "D.21", "tipo": "directo", "notas": "Corrige a" },
    "eli:transposes": { "np": "D.22", "tipo": "directo", "notas": "Transposición de directivas" },
    "eli:related_to": { "np": ["D.11","D.12"], "tipo": "parcial", "notas": "NP distingue concordancia vs. conflicto" },
    "eli:consolidates": { "np": ["E.2","E.3"], "tipo": "parcial", "notas": "NP tiene modelo de versiones más detallado" },
    "eli:consolidated_by": { "np": ["E.2","E.3"], "tipo": "parcial", "notas": "Inverso de consolidates" }
  },
  "gaps_eli": {
    "eli:uri_schema": { "prioridad": "baja", "razon": "Metadato técnico de implementación" },
    "eli:relevant_for": { "prioridad": "baja", "razon": "A.14 cubre ámbito territorial" },
    "eli:in_force": { "prioridad": "media", "razon": "C.1-C.20 son más detallados; se puede mapear" },
    "eli:date_no_longer_in_force": { "prioridad": "media", "razon": "No existe en NP; útil para extinción conocida" },
    "eli:cites": { "prioridad": "media", "razon": "NP no tiene elemento para citas textuales" },
    "eli:applies": { "prioridad": "baja", "razon": "D.11 cubre parcialmente" },
    "eli:version": { "prioridad": "media", "razon": "E.2 distingue original/consolidada" },
    "eli:version_date": { "prioridad": "baja", "razon": "E.9 es similar pero no idéntico" },
    "eli:published_in": { "prioridad": "baja", "razon": "A.6 y A.11 cubren parcialmente" },
    "eli:published_in_format": { "prioridad": "baja", "razon": "G.3 cubre parcialmente" },
    "eli:is_realized_by": { "prioridad": "baja", "razon": "Metadato FRBR conceptual" },
    "eli:is_embodied_by": { "prioridad": "baja", "razon": "Metadato FRBR conceptual" },
    "eli:is_part_of": { "prioridad": "baja", "razon": "B.2-B.8 cubren estructura jerárquica" },
    "eli:is_member_of": { "prioridad": "baja", "razon": "E.3 cubre parcialmente" },
    "eli:is_about": { "prioridad": "media", "razon": "A.15 cubre ámbito material" },
    "eli:is_another_publication": { "prioridad": "baja", "razon": "Metadato específico de múltiples publicadores" }
  },
  "mapeo_lexml_np": {
    "Identificação": { "np": ["A.1","A.2","A.3","A.12"], "estado": "mapeado" },
    "Contexto (FRBR)": { "np": ["A.25","E.1","E.2","B.19"], "estado": "mapeado" },
    "CicloDeVida": { "np": ["A.7","A.8","A.9","C.1-C.20","E.3-E.9"], "estado": "mapeado" },
    "EventosGerados": { "np": ["D.1-D.6","D.19-D.22"], "estado": "mapeado" },
    "Notas": { "np": ["G.7","E.11"], "estado": "mapeado" },
    "Recursos": { "np": ["B.13","G.3"], "estado": "mapeado" },
    "MetadadosProprietario": { "np": ["G.15","G.16","G.17"], "estado": "mapeado" }
  },
  "gaps_lexml": {
    "Fórmulas (MathML)": { "prioridad": "baja", "razon": "NP no diseñado para contenido matemático" },
    "Assinatura digital": { "prioridad": "baja", "razon": "A.17 cubre firma física" },
    "Componentes URN (localidade, autoridade, data)": { "prioridad": "baja", "razon": "Sintaxis específica de URN; A.5, A.7, A.14 cubren semántica" }
  }
}
```

## 6.  RECOMENDACIONES PARA CERRAR GAPS
# ───────────────────────────────────────────────────────────────────────────────

### 6.1  Alta prioridad (interoperabilidad digital)

| # | Acción | Elemento NP afectado | Esfuerzo |
|---|--------|----------------------|----------|
| 1 | Agregar A.26: `eli_uri` — URI ELI completa de la norma | A | Bajo |
| 2 | Agregar A.27: `eli_ontology_version` — Versión de la ontología ELI usada | A | Bajo |
| 3 | Agregar C.21: `fecha_perdida_vigencia` — Fecha en que dejó de estar en vigor | C | Bajo |
| 4 | Agregar D.23: `citas_textuales` — Normas citadas textualmente en el texto | D | Medio |
| 5 | Agregar D.24: `conformidad_no_vinculante` — Normas con las que se conforma sin transposición | D | Bajo |

### 6.2  Media prioridad (enriquecimiento del análisis)

| # | Acción | Elemento NP afectado | Esfuerzo |
|---|--------|----------------------|----------|
| 6 | Agregar E.13: `version_eli` — Estado de versión según vocabulario ELI | E | Bajo |
| 7 | Agregar E.14: `fecha_validez_version` — Punto en el tiempo donde la descripción es válida | E | Bajo |
| 8 | Agregar A.28: `tema_skos` — Tema con URI de vocabulario controlado | A | Medio |
| 9 | Agregar A.29: `jurisdiccion_uri` — Jurisdicción con URI de autoridad | A | Bajo |
| 10 | Mapear C.1-C.20 a los 3 estados ELI (in_force, partially_in_force, not_in_force) | C | Bajo (tabla de conversión) |

### 6.3  Baja prioridad (metadatos técnicos)

| # | Acción | Elemento NP afectado | Esfuerzo |
|---|--------|----------------------|----------|
| 11 | Documentar que el modelo FRBR de ELI (Work/Expression/Format) no se implementa en NP | Documentación | Bajo |
| 12 | Documentar que las relaciones de parte (is_part_of/has_part) se modelan como estructura interna en NP | Documentación | Bajo |
| 13 | Agregar nota técnica sobre URI schema en G.15 (metodología) | G | Bajo |

## 7.  COMPATIBILIDAD CON FUTURAS VERSIONES DE ESTÁNDARES
# ───────────────────────────────────────────────────────────────────────────────

ELI está en evolución (versión 1.1 activa, 1.3 en desarrollo). El sistema NP
está diseñado para absorber nuevas propiedades sin reestructuración mayor:

• Las categorías A, D, E son las más susceptibles de recibir nuevos elementos
  por evolución de ELI.
• El esquema JSON (schema-norma.json) usa `additionalProperties: true` en
  las definiciones de fase, permitiendo agregar campos sin romper validación.
• El modelo relacional tiene campos extensibles (`MetadadosProprietario` en
  LexML; `notas` en todas las tablas NP).

## 8.  FUENTES DE REFERENCIA
# ───────────────────────────────────────────────────────────────────────────────

1. [ELI] European Legislation Identifier — Ontology v1.1
   https://data.europa.eu/eli/ontology

2. [ELI-Tech] ELI — A Technical Implementation Guide
   https://op.europa.eu/documents/2050822/2138819/ELI+-+A+Technical+Implementation+Guide.pdf

3. [ELIdata] ELIdata.es — Ontología y metadatos
   https://www.elidata.es/documentacion_tecnica/ontologia.php

4. [ELI-EP] ELI-EP Application Profile v1.3
   https://europarl.github.io/eli-ep/1.3/

5. [BOE-ELI] Implementación ELI en España (BOE)
   https://www.boe.es/legislacion/eli.php

6. [LexML-1] LexML Brasil — Parte 1: Modelo de Referência (FRBR)
   https://projeto.lexml.gov.br/documentacao/Parte-1-Modelo-de-Referencia.pdf

7. [LexML-2] LexML Brasil — Parte 2: URN
   https://projeto.lexml.gov.br/documentacao/Parte-2-URN.pdf

8. [LexML-3] LexML Brasil — Parte 3: XML Schema
   https://projeto.lexml.gov.br/documentacao/Parte-3-XML-Schema.pdf

9. [LexML-4] LexML Brasil — Parte 4: OAI-PMH
   https://projeto.lexml.gov.br/documentacao/Parte-4-OAI-PMH.pdf

10. [Irish-ELI] Implementación ELI en Irlanda (eISB)
    https://www.irishstatutebook.ie/pdf/ELI_URI_schema.pdf

# ───────────────────────────────────────────────────────────────────────────────
# END OF VALIDACIÓN CRUZADA ELI/LEXML
# ───────────────────────────────────────────────────────────────────────────────
