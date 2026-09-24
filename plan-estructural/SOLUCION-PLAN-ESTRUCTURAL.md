# SOLUCIÓN POR ÍTEM DEL PLAN ESTRUCTURAL
## Cada problema detectado → control estructural → herramienta asignada → prueba del control

> **Regla rectora:** ningún control entra al plan sin su prueba de verificación automática.
> "100% servirá" = el control es *fail-closed* y *testeable*; el despliegue queda bloqueado
> hasta superar el 100% de los casos de oro. Las clases de fallo no cubiertas por los casos
> de oro se absorben mediante el registro de incidentes y la evolución del plan (sección 4).
> Depende de: `PLAN-ESTRUCTURAL-AGENTES-LLM.md` (v1.0).

---

## 1. LA MÉTRICA DE SELECCIÓN DE HERRAMIENTAS (por qué cada herramienta y no otra)

Ninguna herramienta se elige "a dedo". Candidatas se puntúan 0–2 por criterio; los criterios
**V** y **F** son *obligatorios* (gate) para todo artefacto que toque la verdad.

| Criterio | Peso | Pregunta que responde |
|---|---|---|
| **V** Verificabilidad | ×3 | ¿Un script puede validar el artefacto sin LLM? |
| **F** Fail-closed | ×3 | ¿Rechaza entradas malformadas en vez de tolerarlas? |
| **D** Determinismo | ×2 | ¿Mismo input → mismo output siempre? |
| **A** Auditabilidad humana | ×2 | ¿Un humano puede juzgarlo en un diff? |
| **G** Diff/versionado | ×2 | ¿Es texto plano con diff útil? |
| **E** Madurez/ecosistema | ×1 | ¿Existen validadores y librerías probadas? |
| **S** Superficie de dependencia | ×1 | ¿Pocas dependencias externas? |
| **L** Límites de escala conocidos | ×1 | ¿Sus límites están documentados y son aceptables? |

### Comparaciones resueltas con la métrica (demostración de que discrimina)

**Configuración legible por humanos + validable por máquina → YAML (no JSON, no TOML).**
YAML gana por comentarios nativos (A=2 vs JSON=1) y por validador nativo del propio stack
(dsh usa schemastery con fail-loud al cargar: un typo falla el arranque). JSON queda para
artefactos de intercambio máquina-máquina (no necesitan comentarios, parseador built-in).

**Registro de evidencia → JSONL append-only (no SQLite, no Markdown).**
Aunque SQLite puntúa igual en V/F/D, el registro de evidencia prioriza G (diff línea por línea)
y auditoría append-only: JSONL gana 16–13. La misma familia de problema con pesos distintos
produce ganador distinto: para el **índice del corpus** (donde el motor de consulta pesa más
que el diff) gana SQLite FTS5. La métrica decide por caso, no por moda.

**Índice del corpus → SQLite FTS5 (no grep solo, no JSON plano, no grafo).**
A 90 archivos, ripgrep *basta* en velocidad — se reconoce. Pero el índice gana por
**estructura**: segmentación por artículo + metadatos (jerarquía, vigencia) que grep no da.
Control diferencial incluido: el índice debe devolver los mismos resultados que ripgrep en
las consultas de oro; discrepancia = índice inválido. Grafo: rechazado (las consultas son
precedencia + fecha, no recorrido multi-salto; D-graph no justifica su dependencia).

**Schemas de salida → JSON Schema (no pydantic, no "prompt más detallado").**
"Por favor responde en JSON" puntúa V=0, F=0: rechazado por gate. pydantic puntúa igual que
JSON Schema pero es Python-only: el mismo schema debe validar en el workflow (JS) y en el
runner de pruebas (Py) sin duplicar clases de modelo → JSON Schema draft 2020-12.

---

## 2. KIT DE ARTEFACTOS (la arquitectura que sostiene las 35 soluciones)

| Artefacto | Herramienta | Ítems que sostiene |
|---|---|---|
| `AGENTS.md` | Markdown versionado (git) | 4, 14, 29 |
| `constitucion/parametros.yml` | YAML + schemastery | 10, 17, 22, 3 |
| `corpus/index.sqlite` (FTS5) + `corpus.manifest.json` | SQLite + SHA-256 | 2, 8, 16, 21 |
| `evidencia/registro.jsonl` | JSONL + validación por línea | 1, 12, 34 |
| `schemas/*.json` | JSON Schema (ajv + python-jsonschema) | 12, 23, 35 |
| `pruebas/oro/*.json` + `pruebas/runner.py` | JSON + pytest | 1, 2, 5, 13, 24, 29 |
| `runs/<id>/manifest.json` | JSON + git | 15, 27, 34 |
| `DECISIONES/ADR-*.md` | Markdown (Architecture Decision Records) | 18 + evolución |
| `DECISIONES/vacios.md` | Markdown | 35 |
| Tool registry + sandbox + approval | YAML + dsh nativo (bwrap/Landlock/Seatbelt) | 11, 30, 31 |
| Session log / resume | dsh nativo (session.v3.jsonl.zstd) | 19, 20, 34 |
| Verificación 2 pasos | dsh workflow + skills versionadas | 1, 13, 24 |
| Lotes | dsh headless + presupuesto YAML | 3, 28 |
| Escaneo de secretos | gitleaks en CI | 31 |

---

## 3. LAS 35 SOLUCIONES (problema → control → herramienta → PRUEBA)

### A. Naturaleza del modelo

**1. Alucinan** → Evidencia obligatoria por schema: ningún claim relevante parsea sin
{cita textual, fuente, localización}. Verificador ciego en segundo paso.
*Herramientas:* JSON Schema + workflow 2 pasos + `evidencia/registro.jsonl`.
*Prueba:* gold set con trampas (claims falsos con cita inventada); el verificador debe
refutar el 100%. Despliegue bloqueado si falla una sola trampa.

**7. Motor probabilístico** → El LLM solo interpreta; todo cálculo, conteo y transformación
va a código. Regla de oro versionada: *"¿un script de 10 líneas lo haría? Entonces es del script."*
*Herramientas:* Python + pytest.
*Prueba:* casos de cálculo exacto resueltos por script; test falla si el resultado pasó por el modelo.

**12. Confianza estilística** → Schema hace imposible afirmar sin evidencia: campo `evidencia`
es `required` y debe contener cita verificable, no placeholder.
*Herramientas:* JSON Schema (fail-closed por construcción).
*Prueba:* validador rechaza output sin evidencia real (fuzzing de campos vacíos).

**13. Sycofancia** → Verificador ciego: nunca recibe la hipótesis del usuario, solo
{claim, cita}; disenso obligatorio en constitución.
*Herramientas:* plantilla de verificación versionada (skill dsh) + workflow.
*Prueba:* gold cases cuya respuesta verdadera *contradice* lo sugerido; el sistema debe disentir.

**14. Atención diluida** → Constitución corta (tope de tamaño automático) + fases con agente
fresco (spawn) cuando la fase previa no aporta contexto; fork solo con justificación escrita.
*Herramientas:* `AGENTS.md` + política spawn/fork en `parametros.yml` + dsh subagent.
*Prueba:* CI mide tamaño de constitución; decisión spawn/fork registrada en manifiesto (auditable).

**15. No deterministas** → Manifiesto por corrida: hash de prompt, versión de corpus, modelo,
temperatura, schema version.
*Herramientas:* `runs/<id>/manifest.json` + git.
*Prueba:* re-ejecución desde manifiesto → resultado comparable; doble corrida en muestra con
reporte de diff (divergencia = zona inestable marcada).

**16. Corte de conocimiento** → El corpus versionado es la única fuente temporal; cada evidencia
referencia el hash del corpus contra el que habló.
*Herramientas:* `corpus.manifest.json` (SHA-256 de cada norma).
*Prueba:* script rechaza cualquier evidencia cuyo `corpus_hash` no exista en el manifiesto vigente.

### B. Reglas y comportamiento

**4. Siguen reglas** → Reglas viven en `AGENTS.md`/skills versionadas (git), nunca solo en chat.
*Herramientas:* dsh skills + git.
*Prueba:* sesión nueva contiene las reglas (test de presencia); diff entre versiones visible.

**5. Decaimiento de reglas** → Enforcement estructural: la regla crítica se expresa como
validador/sandbox/approval, no como texto. La regla escrita orienta; la estructura obliga.
*Herramientas:* JSON Schema + dsh sandbox/approval.
*Prueba:* **prueba negativa obligatoria por regla crítica**: existe un caso que debe fallar
precisamente porque la regla se incumplió. Sin prueba negativa, la regla no cuenta como control.

**17. Goal drift** → Criterios de aceptación congelados por fase en YAML; script compara
entregables contra criterios; divergencia detiene la fase.
*Herramientas:* `parametros.yml` + script de diff de alcance.
*Prueba:* entregar algo fuera de criterios provoca stop automático (test con entregable extra diseñado).

**18. Correcciones olvidadas** → Tras cada corrección aceptada: ADR + actualización de la regla
correspondiente antes de cerrar la sesión.
*Herramientas:* `DECISIONES/ADR-*.md` + git.
*Prueba:* checklist de cierre — toda corrección del session log tiene ADR o regla asociada (revisión humana firmada).

### C. Memoria y contexto

**8. Mala memoria** → Memoria externa poseída por el humano: índice SQLite + evidencia JSONL +
constitución. Nada crítico vive en el contexto del modelo.
*Herramientas:* SQLite + JSONL + `AGENTS.md`.
*Prueba:* test de continuidad — sesión nueva reconstruye el estado leyendo archivos, sin pérdida.

**10. Carga bajo demanda** → Índice previo + recuperación selectiva con tope de tokens por consulta.
*Herramientas:* SQLite FTS5 + límite en `parametros.yml`.
*Prueba:* medición por consulta; exceder el tope aborta con mensaje (fail-closed, no silencioso).

**19. Sin estado entre llamadas** → Estado en archivos por etapa; reanudar = leer último
checkpoint válido.
*Herramientas:* layout de etapas + `state.json` validado por schema.
*Prueba:* test de corte — matar la corrida a mitad y reanudar produce el mismo resultado final.

**20. Sesiones largas degradan** → Fases con agente fresco; política spawn/fork escrita y registrada.
*Herramientas:* dsh subagent + manifiesto de corrida.
*Prueba:* auditoría del manifiesto: toda decisión de fork tiene justificación escrita (muestreo).

### D. Verdad y evidencia

**2. Fuente de verdad** → Corpus delimitado; cita greppeable obligatoria (archivo + artículo +
texto); taxonomía de veredicto con rotuladores `EXTERNO_NO_VERIFICADO` / `NO_ENCONTRADO`.
*Herramientas:* `AGENTS.md` + enums en JSON Schema.
*Prueba:* gold cases de "no está en el corpus" → el sistema debe devolver `NO_ENCONTRADO`
(el 100% de esa clase; inventar = fallo de despliegue).

**21. GIGO** → El índice se valida *antes* de cualquier prompt: control diferencial contra ripgrep.
*Herramientas:* SQLite FTS5 + script diferencial.
*Prueba:* en las consultas de oro, índice y ripgrep deben coincidir; discrepancia invalida el índice.

**22. Contradicciones** → Política de precedencia escrita (jerarquía normativa, vigencia,
especialidad); ante conflicto el sistema **reporta** conflicto + ganador según regla, nunca elige por intuición.
*Herramientas:* `parametros.yml` + schema de salida con campos de conflicto.
*Prueba:* casos oro con conflicto diseñado → ganador correcto según la regla escrita (test).

**23. Salida estructurada** → JSON Schema + validación automática + reintento acotado del paso.
*Herramientas:* JSON Schema (ajv en workflow, python-jsonschema en runner).
*Prueba:* fuzzing de campos (mutaciones tipo, omisiones) → todo debe fallar validación.

**24. Auto-verificación insuficiente** → Generador ≠ verificador, siempre; veredictos
`SOSTENIDO | REFUTADO | INSUFICIENTE`; `INSUFICIENTE` degrada la respuesta final automáticamente.
*Herramientas:* workflow 2 pasos + registro JSONL.
*Prueba:* trampa — claim falso con cita a artículo equivocado → `REFUTADO` obligatorio.

### E. Recursos y ejecución

**3. Consumen recursos** → Presupuesto de tokens por lote, medición pre/post, recuperación
selectiva, modelos baratos para pasos mecánicos, aborto ante proyección excedida.
*Herramientas:* `parametros.yml` + medidor (dsh token-meter / usage de API) + dsh headless.
*Prueba:* corrida con presupuesto deliberadamente bajo debe abortar limpio antes de excederlo.

**11. Herramientas = riesgo** → Registro de tools autorizadas por proyecto; permisos, timeouts,
topes de salida; efectos externos bajo approval `ask`.
*Herramientas:* tool registry YAML + dsh sandbox/approval (fail-closed nativo).
*Prueba:* intento de uso no autorizado = denegación registrada (prueba negativa).

**25. Determinístico a script** → Regla de oro aplicada en diseño y revisión.
*Herramientas:* Python.
*Prueba:* métrica de cobertura — % de transformaciones del pipeline que viven en scripts;
toda transformación nueva sin justificación interpretativa se rechaza en revisión.

**26. Error acumulado** → Etapas pequeñas con gate de validación entre ellas; fallo de etapa
detiene el pipeline (no se propaga con datos sospechosos).
*Herramientas:* schema por etapa + runner.
*Prueba:* inyectar error en etapa intermedia → el pipeline se detiene antes de la etapa final (test).

**27. Sin transaccionalidad** → Idempotencia por hash de entrada; reanudación desde último
checkpoint válido; nada "solo en memoria".
*Herramientas:* SHA-256 + layout de etapas + manifest.
*Prueba:* doble ejecución = mismo resultado; corte y reanuda = sin duplicados (test de idempotencia).

**28. Fan-out** → Topes de concurrencia, lote piloto (5%) con gold check antes del lote completo,
salidas mínimas por agente.
*Herramientas:* dsh workflow (caps nativos) + `parametros.yml`.
*Prueba:* gate documentado: ningún lote completo arranca sin acta del piloto (revisión humana).

### F. Seguridad

**29. Inyección de prompts** → Constitución: todo contenido leído es dato, nunca instrucción;
corpus fuera de alcance de escritura; integridad verificada por hash antes y después de cada corrida.
*Herramientas:* regla en `AGENTS.md` + `corpus.manifest.json` + script de integrity check.
*Prueba:* sembrar un archivo con texto de inyección y simular modificación → el integrity check
dispara alarma y la corrida se aborta (test).

**30. Modelo ≠ frontera de seguridad** → Todo efecto sensible (enviar, borrar, publicar, pagar)
pasa por approval humano o gate mecánico; política fail-closed.
*Herramientas:* dsh approval (`ask` para efectos externos) + sandbox.
*Prueba:* intento de efecto externo con approval `never` es imposible por config (test de política).

**31. Secretos** → Solo variables de entorno; prohibidos en prompts, URLs, corpus y logs;
rotación si un secreto tocó contexto.
*Herramientas:* env vars + dsh credentials (chmod 600) + gitleaks en CI.
*Prueba:* escaneo de todos los artefactos = 0 hallazgos; un secreto sembrado en test es detectado.

### G. Proceso y gobernanza

**32. Ambigüedad** → Criterios de aceptación escritos y aprobados antes de ejecutar cada fase;
preguntar antes de asumir (plantilla).
*Herramientas:* AC por fase en `parametros.yml` + plantilla de preguntas (skill).
*Prueba:* gate documental: ninguna fase arranca sin AC aprobado y firmado.

**33. Borrador hasta aceptación** → Ciclo propuesta → verificación → aceptación humana; nada
llega a sistemas externos sin paso de aceptación.
*Herramientas:* procedimiento + dsh approval + dsh present (deliverables firmados).
*Prueba:* envío externo simulado exige approval (test); artefacto sin aceptación no sale del workspace.

**34. Observabilidad** → Manifiesto por corrida + evidencia adjunta + session log nativo
replayable. Todo resultado trae su receta de reproducción.
*Herramientas:* `runs/<id>/manifest.json` + dsh session log + `evidencia/registro.jsonl`.
*Prueba:* re-run desde manifiesto reproduce el veredicto (test de reproducibilidad).

**35. "No encontrado" es válido** → Enum lo permite; índice de vacíos (`DECISIONES/vacios.md`)
lo registra como hallazgo; nunca penalizado.
*Herramientas:* JSON Schema + vacios.md.
*Prueba:* gold cases de vacío → `NO_ENCONTRADO` el 100% de las veces; inventar = fallo de clase.

---

## 4. EVOLUCIÓN DEL PLAN (registro y escalamiento cuando la tecnología cambie)

**Principio:** ninguna herramienta es óptima para siempre. Toda adopción queda registrada con
su matriz de evaluación (sección 1) y su **disparador de re-evaluación**, de modo que mejorar
el plan es un procedimiento, no una reconstrucción.

**4.1 Registro (obligatorio por adopción)**
- Cada herramienta adoptada tiene un ADR en `DECISIONES/`: contexto, candidatas evaluadas,
  matriz de puntajes con fecha, ganadora, consecuencias, **disparador de re-evaluación**.
- El plan entero versionado en git; `CHANGELOG` del plan a nivel de ítems.

**4.2 Disparadores de re-evaluación (cualquiera basta)**
1. **Calendario:** revisión semestral del plan, aunque nada falle.
2. **Evento tecnológico:** aparece candidata nueva / estándar relevante / fin de soporte de una adoptada.
3. **Escala:** se cruza un umbral registrado (p.ej. corpus > 500 normas, latencia de consulta > 2 s,
   presupuesto por norma > tope) — umbrales viven en `parametros.yml`.
4. **Fallo:** cualquier incidente en producción → automáticamente: caso de oro nuevo que lo
   capture + control nuevo + ADR. El fallo alimenta el plan; no se archiva sin transformarlo.

**4.3 Puerta de ingreso de tecnología candidata (piloto)**
Ninguna herramienta entra por argumento: debe (a) superar en la misma matriz al incumbente,
(b) pasar los casos de oro existentes, (c) superar un piloto sobre subconjunto real con
métricas antes/después registradas en ADR. Empate = se queda el incumbente (inercia justificada:
costo de cambio conocido > beneficio incierto).

**4.4 Métricas del plan mismo (cómo sabemos que el plan está sano)**
- Cobertura: % de los 35 ítems con control **y** prueba activas (meta: 100%, revisado por CI).
- Fortaleza: pass rate del gold set (gate de despliegue: 100% en clases críticas: trampas de
  alucinación, vacíos, contradicciones).
- Costo real: tokens/norma procesada y tiempo/norma (tendencia por ADR, no por percepción).
- Calidad de salida: % de veredictos con evidencia completa y verificador `SOSTENIDO`.
- Incidentes: conteo por clase + tiempo entre incidente y caso-de-oro-nuevo (debe tender a 0).

---

## 5. ESTADO

- [x] Gold set inicial (trampas de alucinación, vacíos, contradicciones, cálculos) — **HECHO 2026-09-23**
  (25 casos sobre Ley 142 de 1994: 16 citas, 4 conteos, 5 negativos; verificado contra el
  corpus 25/25; ver `sistema/oro/` y `DECISIONES/ADR-0005-paso4-set-de-oro.md`)
- [ ] `parametros.yml` con esquema y umbrales de re-evaluación — pendiente (decisión del humano)
- [x] Runner de pruebas + CI mínimo — **runner HECHO 2026-09-23** (`sistema/scripts/puerta.py`:
  cadena integrity→diferencial→oro→NP en orden, fail-closed probado rojo y verde;
  CI pendiente de `git init`, decisión del humano)
- [x] ADR-0001 (este documento y su matriz) — **HECHO 2026-09-23** (`DECISIONES/ADR-0001-evaluacion-procesador.md`)
- [x] Corpus manifest + índice FTS5 + control diferencial — **HECHO 2026-09-23**
  (90 archivos / 1.811 chunks; reconstrucción lossless 0 fallos; FTS5==fuerza bruta 30/30;
  FTS5⊆rg 15/15; ver `DECISIONES/ADR-0002-paso1-corpus.md`)

*Ninguna fase de proyecto arranca hasta que las 5 casillas estén marcadas y verificadas.*
