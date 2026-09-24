# Verificación contra fuente primaria — método y estado

Herramienta: `sistema/scripts/verificar_fuente.py` (determinista, sin IA, fail-closed).

## Método

1. **Limpieza** de cada lado, quitando lo que no es texto legal: muebles de
   página (EVA/Gestor), enlaces `javascript:` (etiquetas de anotaciones),
   bloques de anotación del gestor/SUIN que el corpus trae en línea
   (Jurisprudencia, Concordancias, Doctrina, Texto del Proyecto de Ley
   Anterior…), imágenes, numeración de página suelta, filas separadoras de
   tablas (el contenido de las tablas se conserva como texto).
2. **Normalización** `fold()`+`plano()` (la misma de todo el sistema).
3. **Segmentación por artículo** en ambos lados (clave = número; los marcadores
   tipo "Artículo CONDICIONALMENTE exequible" no abren segmento).
4. **Comparación artículo a artículo**: `exacto` (igual normalizado) |
   `casi` (similitud ≥ 0.98) | `divergente` (con evidencia del primer diff).
   Claves duplicadas (p. ej. marcador INEXEQUIBLE + artículo real) se
   emparejan por mejor similitud.
5. **Veredicto fail-closed**: `VERIFICADA` solo si ningún artículo del corpus
   queda ausente o divergente. La duda nunca se reporta como match.

## Clases de divergencia (lección del primer ciclo)

| Clase | Ejemplo | Acción |
|---|---|---|
| Contenido perdido en el corpus | Ley 1581 art. 26: faltan literales d), e), f) y parágrafos | **Crítico**: corrige el corpus (errata con evidencia) |
| Aparato de anotaciones | corpus trae Jurisprudencia/Concordancias en línea; la página, en ventanas | Se omite en ambos lados; no afecta el veredicto |
| Etiquetas de anotación en línea | "Texto del Proyecto de Ley Anterior)", "Concordancias)" sueltos | Se eliminan (enlaces javascript) |
| Bloque de sanción entre espejos | art. 30 Ley 1581: firmas distintas según el espejo oficial | Documentar; el cuerpo de la norma es lo que se certifica |
| Corrupción en la fuente misma | gestor CRA: "Decreto 1381 de 20e incorporan…" (salto de texto) | Reportar al emisor; no corregir corpus por eso |
| Fuente truncada por captura | páginas >5 MB del gestor | Reintentar por secciones/PDF; no contar como divergencia |

## Limitaciones conocidas

- Tablas: se comparan como texto lineal (orden de celdas puede divergir por
  formato; ver art. 21 de la Res. 0412 de 2026).
- Páginas del gestor CRA mayores de 5 MB no caben en una captura
  (p. ej. Ley 142 completa): requieren captura por secciones o PDF.
- Desde este entorno, `funcionpublica.gov.co`, `suin.gov.co` y
  `secretariasenado.gov.co` bloquean al capturador (WAF). `minvivienda.gov.co`
  y `normas.cra.gov.co` sí responden.

## Estado por archivo (ledger.json)

| Archivo | Estado | Detalle |
|---|---|---|
| ley_1581_de_2012.md | NO_VERIFICADA | 28/30 artículos verificados (25 exactos + 3 casi ≥0.996). **H1**: art. 26 truncado en el corpus (faltan d) e) f) y 2 parágrafos — hallazgo crítico). **H2**: art. 30, bloque de sanción difiere entre espejos oficiales (cuerpo idéntico). |
| resolucion_0412_de_2026.md | PARCIAL | 20/21 artículos cubiertos verificados (17 exactos + 3 casi). Art. 21 divergente (tabla de fases, formato). Arts. 22–50: fuente truncada por límite de captura. |
| LEY-142-1994.md | PENDIENTE | Disponible en gestor CRA (`ley_0142_1994.htm`) pero excede 5 MB: requiere captura por secciones. |
| Resto (87) | PENDIENTE | Rutas: gestor CRA (13 res. CRA + leyes espejadas), minvivienda.gov.co (PDF, decretos MVCT), SSPD (resoluciones), DNP (CONPES). SUIN/Función Pública requieren canal alterno. |

## Uso

```bash
python3 sistema/scripts/verificar_fuente.py normas_procesar/<norma>.md sistema/verificacion/fuentes/<captura>.txt
# informe: sistema/verificacion/informes/<norma>.json | exit 0 solo si VERIFICADA
```
