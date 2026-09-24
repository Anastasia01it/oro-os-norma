# AUTO-INVESTIGACIÓN TÉCNICA: DEEPSEEK HARNESS (dsh)

> Informe generado por el propio agente en ejecución, mediante introspección directa del runtime,
> el árbol de plugins instalado, la configuración activa y la sesión persistente.
>
> - **Fecha de ejecución:** sesión `session-de30e99f-bd58-48fc-8eca-1aedd75000db`
> - **Versión inspeccionada:** `@deepseek-ai/dsh` **0.1.5-rc.3** (release candidate)
> - **Método:** comandos reales ejecutados contra el runtime vivo (`dsh --version`, `dsh --profile web --dump-config`, lectura de `$DSH_HOME`, descompresión del session log con `zstd`), más inspección de código fuente en el checkout npx y research web para la fase comparativa.
> - **Restricción cumplida:** ninguna clave API, token ni credencial se expone en este documento.

---

## FASE 1: ARQUITECTURA Y ESTADO ACTUAL

### Resultados de Introspección

Comandos reales ejecutados en esta sesión:

```bash
$ dsh --version
0.1.5-rc.3

$ which dsh
/home/atom/.npm/_npx/1e7f6d9597241db0/node_modules/.bin/dsh

$ env | grep -i dsh
DSH_WEB_URL=http://127.0.0.1:3080
DSH_SHELL=1
DSH_SESSION_ID=session-de30e99f-bd58-48fc-8eca-1aedd75000db
DSH_HOME=/home/atom/.dsh

$ ls ~/.dsh/profiles        →  web/   node_modules/
$ cat ~/.dsh/profiles/web/package.json
{
  "name": "dsh-profile-web",
  "dsh": { "profile": { "bundles": [
      "@deepseek-ai/dsh-base",
      "@deepseek-ai/dsh-web-app" ],
      "patchReload": "live" } }
}
```

El perfil activo es **web** (boot desde la GUI en http://127.0.0.1:3080, con `DSH_SHELL=1`).

### Análisis Técnico

#### Diagrama textual de la arquitectura

```
┌────────────────────────────────────────────────────────────────────────────┐
│  dsh CLI (@deepseek-ai/dsh 0.1.5-rc.3, MIT) — único launcher soportado     │
│  bin: lib/bin.js → src/args.ts (gramática) + src/bin.ts (runner)           │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ boot: dsh --profile web
                               ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  PERFIL = pila ordenada de "patch layers" sobre un árbol Cordis vacío      │
│  ~/.dsh/profiles/web/                                                      │
│    1. package.json → dsh.profile.bundles[] (orden de composición)          │
│    2. Bundle @deepseek-ai/dsh-base     (~90 plugins host-plane)            │
│    3. Bundle @deepseek-ai/dsh-web-app  (webserver + UI cliente + APIs)     │
│    4. cordis.patch.yml (capa del usuario)                                  │
│    5. $DSH_HOME/cordis.patch.yml (capa home)                               │
│    6. --patch <path> overlays (repetibles, CLI)                            │
│  patchReload: live → vigila y recarga parches en caliente                  │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ Cordis 4.0.2 (DI container, realms/scope)
                               ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  RUNTIME Cordis — dos planos bien separados                                │
│                                                                            │
│  HOST PLANE (una instancia por proceso, compartida):                       │
│    registries (tools, skills, subagents, jobs), sandbox-policy,            │
│    approval, persistencia de sesiones (JSONL+zstd), storage,               │
│    rutas de modelo LLM, telemetría OTel, webserver, APIs HTTP              │
│                                                                            │
│  AGENT PLANE (una montura por sesión, con realms aislados):                │
│    PRESET (standard/ptc/minimal/cordis) montado bajo el scope de la sesión │
│    → herramientas, persona, secciones de prompt, compactación,             │
│      plan-mode, delegación; aislamiento vía cordis:group + isolate         │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ agent loop (dsh-agent-loop)
                               ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  AGENTE: provider=model route · model=k2p6 (Kimi via anthropic-messages)   │
│  ciclo: model request → stream → tool calls (sandbox+approval) → repeat    │
│  persistencia: ~/.dsh/sessions/<workspace-slug>/<id>/session.v3.jsonl.zstd │
└────────────────────────────────────────────────────────────────────────────┘
```

#### El ciclo de agente y el rol de Cordis

`dsh-agent-loop` es el driver por defecto: crea agentes frescos o reanuda sesiones persistidas y conduce cada turno como **"call model, run tools, repeat"** (cita del README). Soporta `maxParallelToolCalls` (default 10) para llamadas paralelas seguras. La cancelación preserva el texto ya entregado por stream.

**Cordis** (`@deepseek-ai/cordis` 4.0.2, con plugins oficiales `loader`, `include`, `timer`, `hmr`, `group`) es el contenedor de inyección de dependencias sobre el que TODO se construye:

- Cada capacidad es una **fila** (plugin) en un YAML (`cordis.yml` / `*.cordis.yml`).
- El sistema de **realms/ámbitos** (`isolate:`) decide el ciclo de vida: una fila publica servicios en el realm raíz (proceso-global) o en un realm de entrada (privado por sesión/preset). El preset `standard` documenta explícitamente que un servicio publicado fuera de un realm aislado **colisiona entre presets**, y `dsh-agent-presets` **rechaza el montaje** en ese caso. Los labels unen realms; no agrupan instancias.
- Los patches se aplican por **id-targeting** (override de config, `disabled: true`, `inject`), con expresiones `!!js` evaluadas en el runtime.
- `cordis-plugin-hmr` da recarga en vivo de los patches de perfil (`patchReload: live`).

#### Estado, sesiones y aislamiento

Verificado sobre la sesión real en curso (`session-de30e99f-bd58-...`):

```bash
$ ls ~/.dsh/sessions/--home-atom-...-Norma--/session-de30e99f-bd58-48fc-8eca-1aedd75000db/
session.lock  session.v3.jsonl.zstd        # 129 KB comprimido, formato v3

$ zstd -dc session.v3.jsonl.zstd | head -3
{"type":"session","version":3,"id":"session-de30e99f...","cwd":".../Norma",
 "isSeeded":false,"delegationDepth":0,"agentPreset":"standard"}
{"type":"permission/preset","seq":0,...,"data":{"preset":"workspace-write"}}
{"type":"sandbox/mode","seq":1,...,"data":{"mode":"workspace-write"}}
```

- **Persistencia:** log de eventos append-only JSONL comprimido con **zstd** (magic `28 b5 2f fd`), versionado (`version: 3`), con `session.lock` de exclusión. La reanudación es **reproducción de eventos** (`effective = explicit grant ?? fold(events) ?? deployment default`).
- **Aislamiento por sesión:** cada sesión tiene cwd inmutable, modo sandbox propio, política de approval propia y preset propio; dos sesiones nunca ven el estado de la otra (verificado en el README de `dsh-sandbox-policy`).
- **Directorio por workspace:** las sesiones se agrupan bajo un slug del path del workspace (`--home-atom-...-Norma--`).
- **Storage de dominio:** `~/.dsh/storages/` (backend JSON: `workspace.json`, `session_projcache`).
- **Credenciales y settings:** `~/.dsh/.credentials.yaml` (chmod 600) y `~/.dsh/settings.yaml` (chmod 600).

### Plugins activos (árbol compuesto real)

`dsh --profile web --dump-config` produce **539 líneas**. Extracción de los bloques principales:

**Host plane (`@deepseek-ai/dsh-base`, ~90 filas):** timer, llm, deepseek-llm-api-extensions, session, session-log-deepseek, typert-registry/loader/gateway (API gateway), session-title(+llm), user-questions, agent, plugin-package-inventory-deepseek, agent-default-model, jobs-local, llm-retry, settings-file, credentials-local, llm-pi-ai, session-persistence-jsonl, attachment-local, session-query-sqlite, session-projection(+cache), storage(+json,+domain), session-telemetry-otel (OTLP a DeepSeek), subprocess-local, sandbox-local, sandbox-policy, bash-sandbox, pwsh-sandbox, user-approval, permission-presets, shell-env, fs-observation-policy, skill(+badge+filesystem), commands, command-feedback, goal, goal-round-driver, plan-mode, token-meter, compaction-basic, command-compact, subagent(+spawn/fork-in-process), timeout-policy, spill-local, spill-policy, session-checkpoint-policy, tool-result-pruner, repeat-tool-reminder, web(+search-deepseek+fetch-http), tools, system-prompt, agent-loop, fs-sandbox, llm-deepseek.

**Web app (`@deepseek-ai/dsh-web-app`):** deshabilita las tools "CLI-facing" base (tool-bash/pwsh/fs/fs-search/jobs/web/subagent/workflow/ralph/todo/goal/skill/present/compaction/command-goal/plan-mode/agent-instructions/tool-result-pruner en la capa host) y añade: code-runtime-worker-thread, message-feedback, session-log-export, open-in-app, workspace, session-reference, file-reference-local, session-stats, session-turn-outline, directory-picker-auto, plugin-inventory, api-session-controller, api-workspace-files/settings/workspace controllers, cordis-host-runner, webserver (gzip), web-runtime, client-hmr, client-modules, client-connection, file-upload, api-remotes, cordis-client-runner, y ~40 módulos de UI cliente (theme, locale, layout, renderer, sidebar, chat, approval, plan, subagent, workflow-run, deliverables, trajectory, agent-preset, settings-*).

**Agent plane (preset `standard`, montado por sesión):** persona, agent-instructions, tool-bash/pwsh, tool-fs, tool-fs-search, tool-jobs, skill-filesystem, tool-skill, command-goal, tool-goal, plan-mode (realm aislado), compaction group (aislado: compaction-basic, command-compact, tool-result-pruner), delegation group (aislado `workflowEngine`: tool-subagent-control, tool-subagent spawn/fork, tool-subagent-codex/claude-code [disabled], workflow-worker-thread, tool-workflow, tool-ralph), tool-ask-user, tool-todo, tool-web, present.

**Paquetes internos instalados:** 241 bajo `@deepseek-ai/*` (todo el monorepo).

### Conclusiones (Fase 1)

1. **No es un binario monolítico**: es un *compositor declarativo*. La unidad de arquitectura es el **perfil** = pila de bundles + parches del usuario; la unidad de ejecución es la **fila Cordis**.
2. **Dos planos (host/agent) con realms aislados** es la decisión de diseño más distintiva: permite que múltiples sesiones con distintos presets coexistan en un proceso sin colisiones de servicios.
3. **Todo es observable**: `--dump-config` muestra el árbol compuesto completo sin bootear; el session log descomprimido muestra cada evento de política.
4. El runtime está **100% desacoplado del proveedor de LLM**: la ruta de modelo activa en esta instalación es **Kimi k2p6** (endpoint `anthropic-messages`), no DeepSeek.

---

## FASE 2: INVENTARIO DE HERRAMIENTAS NATIVAS

### Resultados de Introspección

Fuente primaria: el **catálogo de herramientas de la sesión actual** (preset `standard`, montado para este agente) más los paquetes `@deepseek-ai/dsh-tool-*` instalados. El catálogo vivo de esta sesión:

```
ask_user_question  bash            create_goal   edit          exit_plan_mode
get_goal           glob            grep          interrupt_agent job_kill
job_list           job_output      present       ralph         read
read_image         send_message    skill         subagent      subagent_fork
todo_write         update_goal     web_fetch     web_search    workflow
write
```

### Análisis Técnico — Catálogo por familias

*(Los schemas exactos de entrada/salida por paquete se anexan desde la inspección de código; aquí el catálogo funcional con el contrato que este agente observa en vivo.)*

**1. Shell y procesos**
| Tool | Paquete | Contrato (observado) | Seguridad |
|---|---|---|---|
| `bash` | dsh-tool-bash | `command` (string, obligatorio), `workdir`, `timeoutMs`, `run_in_background`, `sandbox_permissions` (enum) + `justification` solo en reintento de escalación | Ejecución vía dsh-bash-sandbox (bwrap/Landlock/Seatbelt); denegación marcada `[sandbox: file access denied under <mode>]`; escalación = 1 reintento exacto; sin sandbox disponible → `SANDBOX_UNAVAILABLE` (fail-closed) |
| `job_*` (list/output/kill) | dsh-tool-jobs | `job_id`, `wait`, `timeout_ms` | Solo controla jobs del agente dueño; registry host-plane keyed by agent |
| `interrupt_agent` | dsh-tool-subagent-control | `agent_id` (direct child o deeper; deeper = solo cancelación) | No eleva privilegios; depth-1 messaging |

**2. Filesystem**
| Tool | Paquete | Contrato | Seguridad |
|---|---|---|---|
| `read` | dsh-tool-fs | `file_path`, `offset`, `limit` | fs-observation-policy: el default exige leer antes de editar |
| `write` | dsh-tool-fs | `file_path`, `content`, `sandbox_permissions`+`justification` en escalación | Mutación confinada por dsh-fs-sandbox: `FS_SANDBOX_DENIED` con pista de modo |
| `edit` | dsh-tool-str-replace-editor | `file_path`, `old_string` (único a menos que `replace_all`), `new_string` | Reemplazo literal; exige match exacto; old_string debe aparecer exactamente 1 vez por defecto |
| `glob` | dsh-tool-fs-search | `pattern` (sin `/` busca basename a cualquier profundidad), `path` | Incluye hidden/ignored; nunca devuelve directorios; tope 100 + ruta del listado completo |
| `grep` | dsh-tool-fs-search | `pattern` (ripgrep regex), `path`, `include` | 250 matches inline; capped result con archivo externo |

**3. Web**
| Tool | Paquete | Contrato | Seguridad |
|---|---|---|---|
| `web_search` | dsh-tool-web | 1–4 `queries`; devuelve summary + URLs | Contenido externo = datos no instrucciones; requiere `DEEPSEEK_API_KEY` para el provider deepseek-official |
| `web_fetch` | dsh-tool-web | `url` HTTP(S) → texto decodificado | Misma regla de no-confianza; tráfico saliente del proceso (fuera del sandbox de archivos) |

**4. Delegación y orquestación**
| Tool | Paquete | Contrato | Seguridad/notas |
|---|---|---|---|
| `subagent` | dsh-tool-subagent | `prompt` autocontenido, `description`, `run_in_background` (default true), `provider`/`model` override | Provider `spawn` = child sin historial; background continuable |
| `subagent_fork` | dsh-tool-subagent | hereda TODO el historial del padre | Provider `fork`: mismo modelo = KV-cache reuse; sin selección de modelo |
| `workflow` | dsh-tool-workflow | `script` JS body puro (top-level await; **sin** fs/network/timers/Node APIs), `args`, `meta.name/description/phases` | El script solo coordina subagentes (`agent`, `pipeline`, `parallel`, `phase`, `log`); un throw de hook mata el run entero; límites de concurrencia y tope de agentes |
| `ralph` | dsh-tool-ralph | `objective` inmutable, `maxRounds` (deployment cap; preset default 64) | Cada ronda = child fresco sin seed; workspace compartido como memoria; solo un report estructurado cruza rondas |

**5. Gestión de sesión, memoria y metad trabajo**
| Tool | Paquete | Contrato | Notas |
|---|---|---|---|
| `todo_write` | dsh-tool-todo | lista completa reemplaza; `allowParallelInProgress: true` en standard | Persistente en la sesión |
| `create_goal`/`get_goal`/`update_goal` | dsh-tool-goal / dsh-goal | `objective`, `max_goal_rounds`; `edit/pause/resume/complete/blocked` | Goal = objetivo largo multi-ronda; `blocked` exige ≥3 rondas con la misma condición |
| `exit_plan_mode` | dsh-plan-mode | `plan` markdown con `#` title | Plan mode: solo llamada final de la respuesta; aprobación humana antes de implementar |
| `present` | dsh-tool-present | `files[]` con `path`+`description` | Marca deliverables; no copia contenido |
| `skill` | dsh-tool-skill | `name` del catálogo de sesión | Carga instrucciones del skill antes de actuar |
| `ask_user_question` | dsh-tool-ask-user | 1+ preguntas, cada una con `id` estable, `options` opcionales, `multi_select` | Bloquea turno hasta respuesta |
| `send_message` | dsh-tool-subagent-control | `agent_id` (depth-1), `message` | Steer de child running / start de turno en idle/ready |

**6. Sensores**
| Tool | Paquete | Contrato | Notas |
|---|---|---|---|
| `read_image` | dsh-attachment-local | path PNG/JPEG/WebP/GIF; acepta path sin extensión | Downscale automático por el harness antes del request |

### Ejemplos Prácticos (Fase 2)

```bash
# bash: foreground con workdir y timeout
bash(command="pnpm test", workdir="packages/core", timeoutMs=120000)

# bash: background + recolección vía job_output
bash(command="pnpm run build && pnpm run dev:web", run_in_background=true)
# → job id inmediato; luego job_output(job_id, wait=true, timeout_ms=…); job_kill para detener

# Escalación one-shot tras denegación (patrón del tool, no negociación libre):
bash(command="docker compose up -d", sandbox_permissions="workspace-write",
     justification="Necesita crear contenedores fuera del sandbox de archivos.")
```

```json
// edit: reemplazo literal con match único
{"file_path": "src/config.ts", "old_string": "timeoutMs: 60000", "new_string": "timeoutMs: 120000"}

// workflow: script puro de orquestación (sin fs/net en el propio script)
{"meta": {"name": "audit", "phases": [{"title": "scan"}]},
 "script": "const r = await agent('revisa ' + args.dir, {label: 'scan'}); return {findings: r};",
 "args": {"dir": "src/"}}
```

```yaml
# exit_plan_mode: última y única tool call de la respuesta en plan mode
{"plan": "# Migración a v2\n\n## Fase 1: …"}
```

### Matriz de permisos y restricciones (síntesis)

| Capa | read-only | workspace-write | danger-full-access |
|---|---|---|---|
| fs: read/glob/grep/image | ✅ | ✅ | ✅ |
| fs: write/edit | ❌ `FS_SANDBOX_DENIED` | ✅ bajo workspace + temp | ✅ sin límite |
| bash: escritura de archivos | ❌ denegado + marcador | ✅ confinado (bwrap/Landlock/Seatbelt) | ✅ sin confinamiento |
| bash: red / procesos | ⚠️ fuera de garantía del sandbox (declarado) | ⚠️ idem | ⚠️ idem |
| approval policy | `ask` | `ask` | `never` (derivado) |
| escalación | 1 reintento exacto, justificación + prompt de aprobación | idem | n/a (sin approval) |

**Invariants documentados:** fail-closed en sandbox y approval; deny-only en el seam del ejecutor (la concesión vive en la tool layer); doble auditoría o no hay decisión; el modelo nunca ve la UI humana ni los eventos de auditoría — solo outcome + política vigente en el runtime-context snapshot.

### Anexo técnico 2-A — Inventario por paquete (inspección de código, 20 paquetes → 31 herramientas)

Transversal: todas las tools se definen con `defineTool()` de `@deepseek-ai/dsh-tools`; el schema es **por-propiedad** (`required` por campo, no arrays JSON-Schema); la config de plugins usa schemastery con **fail-loud al cargar** (un typo falla el boot, no se ignora). **No hay i18n del texto visible al modelo**: descripciones y prompts están hardcodeados en inglés (`README.i18n.yaml` solo verifica hashes README.md/zh.md).

| Paquete | Tools | Schema (obligatorios con `s`) y límites | Restricciones de seguridad |
|---|---|---|---|
| dsh-tool-bash | `bash` | `command`·`description`, `timeoutMs`, `workdir`, `run_in_background`; escalación: `sandbox_permissions`(enum) + `justification` | Validación no-vacía; escalación resuelta ANTES de ejecutar vía approveEscalation (fail-closed); salida truncada con spill path; marker `[exit code: N]` |
| dsh-tool-bash-persistent | `bash` (alternativa, preset minimal) | solo `command`; maxOutputChars 16000; timeoutMs 300000 | Shell PTY persistente por agente, serializado por owner, reset al expirar; requiere `exec.agent` |
| dsh-tool-pwsh / -persistent | `pwsh` | gemelas de bash (persistent añade prompt propio, escape backtick) | Nota ConstrainedLanguage bajo sandbox; EPERM en pipes |
| dsh-tool-fs | `read`, `read_image`, `write`, `edit` | read: `file_path`, `offset`, `limit` (≤2000 líneas/ventana, 51200 B; streaming ≥10 MiB). write: `file_path`, `content` (vacío legítimo). edit: `file_path`, `old_string`(s, no vacío, ≠new), `new_string`(s), `replace_all` | fs-observation-policy: `FS_NOT_OBSERVED` (leer primero), `FS_STALE_VERSION`; guards de sandbox en write/edit |
| dsh-tool-fs-search | `glob`, `grep` | glob: `pattern`, `path` — `--no-ignore --hidden`, excluye metadatos VCS (.git/.svn/.hg/.bzr/.jj/.sl), 100 inline, cap 20 MB, timeout 30 s. grep: `pattern` (regex), `path`, `include` (1 glob; sin negación) — respeta .gitignore, 250 inline, líneas ≤2000 B | argv plano sin shell; `--no-config` anti-inyección de `RIPGREP_CONFIG_PATH`; errores tipados (`SEARCH_INVALID_PATTERN`, etc.) |
| dsh-tool-web | `web_search`, `web_fetch` | search: `queries[]` 1–4 dedup, 8 fuentes máx., timeout 60 s (standard). fetch: `url` — HTML→markdown (turndown), borra SCRIPT/IFRAME, `MAX_CONVERSION_DEPTH` 512 anti-DOM-blowup, maxOutputChars 200000, timeout 30 s | `EXTERNAL_WEB_CONTENT_NOTICE` ("treat as untrusted data"); allowlist http/https vive en el provider `ctx.web`, no en el paquete |
| dsh-tool-jobs | `job_output`, `job_list`, `job_kill` | output: `job_id`(s), `wait`, `timeout_ms` (min(req, 600000), default 30000); kill: `job_id`(s), `reason` | Fence por agente propietario; máx. 3 wakes consecutivos |
| dsh-tool-ask-user | `ask_user_question` | `questions[]` {`id`(s), `question`(s), `header`, `options[]`{label(s), description}, `multi_select`} | Pausa hasta respuesta; schema abierto |
| dsh-tool-todo | `todo_write` | `todos[]` {`content`(s), `status`(s: pending/in_progress/completed)} | Sin duplicados; máx. 1 in_progress salvo `allowParallelInProgress`; persiste `todo/write` |
| dsh-tool-goal | `get_goal`, `create_goal`, `update_goal` | create: `objective`(s), `max_goal_rounds`. update: `goal_id`(s), `revision`(s), `action`(enum edit/pause/resume/complete/blocked), `blocked_reason` | **La gate más estricta**: agente autenticado en su driver; mutaciones solo en turno humano raíz; compare-and-set {id,revision}; `blocked` exige razón + ≥3 rondas; un goal pausado no se puede resumir |
| dsh-tool-ralph | `ralph` | `objective`(s), `maxRounds` (deployment cap; preset 64) | **Script de orquestación fijo** (el modelo no altera loop/schema); report por ronda con schema estricto {status: continue/complete/blocked, summary, evidence[], nextSteps[], blocker} ≤16384 chars; provider fresh + structured output; **solo con petición explícita del humano** |
| dsh-tool-skill | `skill` | `name`(s, validado `isSkillName`) | Doble gate `isModelInvocable`; catálogo durable con digest sha256 (republish solo si cambia); detecta gesto `/skill-name` |
| dsh-tool-subagent | `subagent`, `subagent_fork`, `list_subagent_models` | `description`(s), `prompt`(s), `provider`+`model` (juntos), `reasoning_effort`, `run_in_background` | maxDepth default **3**; toolFilter allow/deny del hijo; **política durable de rutas LLM por sesión** (ruta no permitida → error); preflight contra LLM vivo; foreground siempre dispose |
| dsh-tool-subagent-control | `send_message`, `interrupt_agent`, `list_agents` | send: `agent_id`(s), `message`(s). interrupt: `agent_id`(s). list: `scope`(children/descendants) | send solo a hijo continuable depth-1 (o al padre si eres hijo residente); interrupt = autoridad de ancestro |
| dsh-tool-workflow | `workflow` | `script`(s: JS top-level await, sin `export const meta`), `meta`(s){name(s), description(s), whenToUse, phases[]}, `args` | Engine endurecido intercambiable; hooks agent/pipeline/parallel/phase/log/args; JSON Schema restringido a type/properties/required/additionalProperties/items/enum/const/oneOf; **sin fs/network/timers**; maxResultChars 50000; stopReason≠completed → error; cancelación + dispose garantizado |
| dsh-tool-present | `present` | `files[]` {`path`(s), `description`} | 1–8 ficheros; deben existir y ser regulares (`FS_NOT_FOUND` con consejo); turno abierto + workspace requeridos; registro durable solo tras resultado no-error |
| dsh-tool-str-replace-editor | `str_replace_editor` — **NO está en standard** (estilo Claude Code) | `command`(enum view/create/str_replace/insert), `path` (**absoluta**), `file_text`, `old_str`, `new_str`, `insert_line`, `view_range` | create no sobrescribe; str_replace exige match único (`FS_AMBIGUOUS_EDIT`); concurrencia optimista `replaceIfVersion`; maxOutputChars 16000 |
| dsh-tool-cordis | 7 tools: `cordis_inspect_list/query/self`, `cordis_define`, `cordis_run`, `cordis_stop`, `cordis_undefine` (preset **cordis**; host-plane) | define: oneOf new{idPrefix `/^[a-z]{3,6}$/`}/existing{pluginId}, `name`, `purpose`, code host/client (≥1 mitad). run: `mode` enum run/update (update de client no autorizado → approval humano) | `requireAgent` en todas; ownership por sesión; precheck de sintaxis `new Function`; sandbox `node:vm` con require/timers/fetch trampeados, `process` undefined, vmTimeoutMs 5000 **solo síncrono**; **el propio README declara el sandbox NO es frontera de seguridad — "treat like bash access"**; in-memory (muere al reinicio) |

**Servicios no-tool que acompañan al catálogo** (evidencia de código): `dsh-plan-mode` (estado durable `plan/mode`; `exit_plan_mode` con review Approve/Keep-planning; la restricción es **solo por texto** — las tools siguen listadas), `dsh-compaction-basic` (umbral 0.8 del contexto, retain 0.16, recuperación de `CONTEXT_WINDOW_EXCEEDED`, transacción bracket-first, reutiliza prefijo caliente del provider), `dsh-token-meter` (medición determinista plegando el log; ~4 chars/token; **cero llamadas al modelo**), `dsh-goal` (1 objetivo por sesión, fases active/paused/blocked/complete, defaultMaxGoalRounds 256, desarmado tras resume/fork), `dsh-session-checkpoint-policy` (checkpoints fail-closed antes de petición modelo, tools con efectos externos, y cada pre-step), `dsh-spill-policy` (head/tail + locator; best-effort: un fallo de spill nunca es error), `dsh-repeat-tool-reminder` (umbrales [3,5,8] por repetición exacta tool+args; advisory, nunca bloquea).

### Conclusiones (Fase 2)

1. El catálogo efectivo es **el del preset**, no el del paquete: la misma instalación expone catálogos distintos por sesión (standard vs minimal vs ptc) porque las tools se registran en el agent-plane.
2. Las herramientas de mayor riesgo (shell, escritura, escalación) pasan por **dos gates independientes**: sandbox-policy (file effects) y user-approval (decisión humana/máquina).
3. La superficie de orquestación (subagent/fork/workflow/ralph/goal) es nativa y de primer orden — no añadidos de plugins de terceros.

---

## FASE 3: MODOS DE EJECUCIÓN Y CONFIGURACIÓN

### Resultados de Introspección

**Configuración activa** (`~/.dsh/settings.yaml`, sanitizada — el archivo real es chmod 600):

```yaml
ui-onboarding:
  welcomeNoticeVersion: 2026-08-13.1
llm-pi-ai:
  providers:
    k2p6:
      apiKeyEnv: K2P6_API_KEY            # la clave vive en el entorno, no en el archivo
      api: anthropic-messages            # dialecto de API
      baseURL: https://agent-gw.kimi.com/coding
      models: [ { id: k2p6, name: k2p6 } ]
agent-default-model:
  provider: k2p6
  model: k2p6
agent-presets:
  default: standard
```

Hallazgos de configuración:
- **La clave API nunca se almacena en el YAML**: `apiKeyEnv: K2P6_API_KEY` referencia una variable de entorno (patrón repetido en `web-search-deepseek` con `DEEPSEEK_API_KEY`).
- **El modelo por defecto NO es DeepSeek**: el deployment usa Kimi k2p6 de Moonshot AI a través del dialecto `anthropic-messages` — prueba directa del agnosticismo de proveedor.
- Las credenciales están en `~/.dsh/.credentials.yaml` (chmod 600), fuera del alcance del modelo.

**Los presets instalados** (evidencia real de `node_modules/@deepseek-ai/dsh-agent-presets/presets/`):

| Preset | Nombre UI (zh) | order | Esencia |
|---|---|---|---|
| `standard` | 标准模式 | 1 | Agente completo |
| `ptc` | PTC 模式 | 2 | standard presentado como SDK TypeScript (`run_code`) |
| `minimal` | 极简模式 | 3 | Shell persistente, herramienta única |
| `cordis` | 创造模式 | 4 | standard + auto-modificación del runtime |

> **Corrección a la premisa de la misión:** la documentación pública de DSH no habla de "Standard / Code / Minimal / Creator". Los 4 presets reales de esta versión son **standard, ptc, minimal y cordis**. El mapeo natural es: *Code* ≈ **ptc** (Program-To-Compose: el modelo compone TypeScript en vez de llamar tools una a una) y *Creator* = **cordis** (创造模式, literalmente "modo creación": el agente puede leer y modificar el harness en el que corre).

### Análisis Técnico — Tabla comparativa de modos

| Dimensión | **standard** | **ptc** | **minimal** | **cordis** |
|---|---|---|---|---|
| Herramientas | bash/pwsh, fs (read/write/edit/glob/grep), jobs, skill, goal, plan-mode, compaction, subagent spawn+fork, workflow, ralph, ask-user, todo, web, present | = standard **menos** `workflow` tool; **más** presentación PTC (`dsh-agent-tool-presentation` mode ptc) | **Solo** shell persistente (`bash`/`pwsh` con PTY, estado persistente entre llamadas) | = standard **más** `tool-cordis` (mount/unmount de plugins en el runtime vivo) + skill `editing-cordis-compositions` |
| Superficie de composición | N llamadas de herramienta por tarea multi-paso | **1 programa TypeScript** (`run_code`) que orquesta N operaciones → menos round-trips | comandos de shell | N llamadas + auto-rewiring del árbol Cordis |
| System prompt | persona + instrucciones (max 64 KiB) | = standard | persona **completa y fija** (`complete: true`): sin runtime-context, sin listeners de ensamblado | persona extendida que explica los dos planos (host/agent) y dónde pertenece cada edición |
| Compactación de contexto | sí (compaction-basic + pruner 8192/4096/1024) | sí | **no** | sí |
| Caso de uso óptimo | Trabajo de codificación general | Pipelines repetitivas de muchos pasos; presupuesto de tokens ajustado | Entornos restringidos/CI; tareas de shell puro; depuración de un comando a la vez | Meta-programación: crear/modificar presets y plugins del propio harness |
| Limitaciones | catálogo grande = más tokens de sistema | requiere el `codeRuntime` del host; si falta, **falla el montaje nombrando el id** | sin fs tools: el modelo debe usar `cat/sed/grep` por shell; sin compactación (contexto crece) | **frontera de confianza, no sandbox**: `cordis_mount` evalúa JS del modelo contra el runtime vivo; equivale a shell access |
| Seguridad | sandbox + approval del host | igual | igual | el propio preset advierte: trátala como shell access |

Los 4 presets comparten el stack host: sandbox-policy (`read-only` | `workspace-write` | `danger-full-access`), approval (`ask` | `never`), spill (maxInlineBytes 50000), timeout-policy, repeat-tool-reminder (umbrales 3/5/8), telemetry OTel.

### Ejemplos Prácticos

Cambiar de preset (vía UI o al crear la sesión); crear un preset propio (del preset `cordis`):

```bash
# presets de usuario viven en ~/.dsh/.agent-presets/<id>/  (NUNCA editar los shipped)
mkdir -p ~/.dsh/.agent-presets/mi-preset
cp -r <install>/agent-presets/standard/* ~/.dsh/.agent-presets/mi-preset/
# editar agent.cordis.yml: deshabilitar filas, añadir las tuyas
```

Cambiar política en caliente (comandos reales soportados por el runtime — observados en el session log como `command/run` con `name: permission`):

```bash
# Dentro de la sesión (o vía comando de la app):
permission workspace-write     # eventos: permission/preset + sandbox/mode + approval/policy
permission danger-full-access  # → sandbox: danger-full-access, approval: never
```

### Conclusiones (Fase 3)

1. Los modos son **composiciones declarativas**, no flags: un preset es un directorio con `preset.yml` (metadatos) + `agent.cordis.yml` (composición del agent-plane).
2. La diferencia clave entre presets es **qué registran en el catálogo del agente y qué aíslan en realms**, no código imperativo.
3. La configuración del modelo es tan portable como un snippet YAML: provider + dialecto de API + baseURL + env-var de clave.

---

## FASE 4: ANÁLISIS COMPARATIVO CON ALTERNATIVAS

### Resultados de Introspección

Investigación con **fuentes primarias** (raw.githubusercontent.com, páginas oficiales de precios, npm registry, GitHub API, archive.org). Nota metodológica auto-referente: `web_search` de este harness **falló por ausencia de `DEEPSEEK_API_KEY`** (limitación #3 documentada en la Fase 6) — la investigación se completó con `web_fetch` directo. Informe completo con URLs en `analisis-agentes-codificacion-2025.md`.

### Tabla comparativa

| Agente | Licencia | Precio | Agnosticismo de modelo | Extensiones | Madurez |
|---|---|---|---|---|---|
| **DeepSeek Harness (dsh)** — *yo* | **MIT** ✅ | OSS gratis; BYOK (esta sesión corre sobre Kimi k2p6, no DeepSeek) | **Total**: el harness está desacoplado; rutas de modelo vía plugins/config | **"Everything is a Plugin"** sobre Cordis (arXiv 2608.25512); skills; presets de agente; MCP; ACP/SDK embebibles | **Developer preview** (repo 2026-08-13; breaking changes anunciados) |
| **Claude Code** (Anthropic) | **Propietaria** — LICENSE.md: "© Anthropic PBC. All rights reserved… Commercial Terms" | Pro ~$20/mes; Max $100/$200; API pay-per-use | **Solo Claude** (Anthropic API, Bedrock, Vertex, Foundry) | MCP cliente, plugins+marketplaces, skills, hooks, subagentes, agent teams; API = Claude Agent SDK | Alta (research feb-2025 → GA may-2025 → web oct-2025) |
| **Cursor** (Anysphere) | Propietaria (closed source, fork de VS Code) | Hobby gratis; Pro $20; Pro+ $60; Ultra $200 | Multi-modelo (GPT/Claude/Gemini/Grok…) | MCP, skills, hooks y marketplace **en planes de pago**; reglas; cloud agents; CLI propio | Alta |
| **OpenAI Codex CLI** | **Apache-2.0** ✅ (Rust) | CLI gratis; incluido con ChatGPT Plus+; o API key | Principalmente OpenAI (gpt-5.x-codex); `model_providers` acepta APIs OpenAI-compatible y modelos locales (Ollama/LM Studio) → **agnóstico parcial** | MCP, AGENTS.md, skills, exec policies, hooks, Codex SDK, GitHub Action | Alta |
| **Gemini CLI** (Google) | **Apache-2.0** ✅ | Gratis: 60 req/min y 1.000 req/día con cuenta Google; Vertex | **Solo Gemini** | MCP, extensiones, custom commands, GEMINI.md, checkpointing | Alta (jun-2025, releases semanales) |
| **Aider** | **Apache-2.0** ✅ | Gratis; pagas tu API key | **Muy agnóstico** (casi cualquier LLM, incl. DeepSeek y locales) | Minimalista: sin MCP nativo; repo map, auto-commits, watch mode | Muy madura (~6,8M installs PyPI) |
| **OpenHands** (ex-OpenDevin) | **MIT** ✅ | OSS gratis self-hosted; Cloud/Enterprise | Agnóstico ("use with any LLM") | Microagents, MCP, **ACP** (orquesta Claude Code/Codex/Gemini), SDK Python | Media-alta (pivote a Agent Canvas) |
| **Crush** (Charm) | **FSL-1.1-MIT** ⚠️ (MIT a los 2 años; hoy no OSI) | Gratis self-hosted; Charm Hyper | Muy agnóstico (OpenAI, Anthropic, Gemini, OpenRouter, Bedrock, Vertex, Azure, **DeepSeek**, locales) | MCP (stdio/http/sse + OAuth), LSP, hooks preliminares | Media (2025) |
| **Amp** (Sourcegraph) | Propietaria | Hobby gratis (BYOK); Individual $20/mes | Agnóstico/BYOK | MCP, plugins, skills, subagentes | Media |

### Análisis por dimensiones

**1. Agnosticismo del modelo.** dsh es el único donde la neutralidad es *arquitectónica*: la ruta de modelo es una fila de configuración (evidencia viva: esta sesión corre Kimi k2p6 por `https://agent-gw.kimi.com/coding` con dialecto `anthropic-messages`, y el bundle trae `dsh-llm-deepseek` y `dsh-llm-pi-ai` como proveederes intercambiables). Claude Code y Gemini CLI son de un solo proveedor; Cursor y Crush son multi-modelo a nivel de producto; Codex acepta providers OpenAI-compatible. Aider y OpenHands empatan con dsh.

**2. Extensibilidad.** dsh es el más *radical*: no hay "sistema de plugins" como feature — la aplicación entera (incluida la UI web, ~40 módulos cliente) es un árbol Cordis componible por el usuario, y un preset de agente es un archivo YAML copiable. Claude Code tiene el ecosistema de extensiones más poblado (marketplaces, Agent SDK). Cursor concentra extensión *de pago*.

**3. Licencia.** MIT de dsh supera a los propietarios (Claude Code, Cursor, Amp) y a Crush (FSL, no-OSI transitoria). Empata con OpenHands (MIT); Apache-2.0 de Codex/Gemini CLI/Aider es equivalente en permisividad práctica.

**4. Costo de operación.** dsh: $0 de software + tu API key (BYOK) + máquina propia. Claude Code/Cursor/Amp: suscripción. Gemini CLI: free tier generoso. Codex: incluido con ChatGPT.

**5. Curva de aprendizaje.** dsh exige entender perfiles/patches/realms (documentación extensa pero densa; los READMEs de paquete son de referencia, no tutoriales). Claude Code y Cursor apuntan a cero-config. Aider es el más simple.

**6. Madurez del ecosistema.** El punto débil objetivo de dsh: developer preview con breaking changes anunciados, sin marketplace de plugins público maduro (topic `dsh-plugin` emergente), frente a GA de todos los competidores. A favor: la publicación npm por paquete (`241` módulos `@deepseek-ai/*`) y la documentación por-paquete generada son un ecosistema ya estructurado.

### FODA de dsh en el mercado

**Fortalezas**
- MIT + BYOK: costo marginal cero, sin lock-in de proveedor ni de licencia.
- Composición declarativa total (Cordis): observabilidad (`--dump-config`), aislamiento por realms, perfiles replicables como texto.
- Agnosticismo real de modelo (Kimi en vivo en este equipo) y de transporte (Anthropic/OpenAI dialects).
- Orquestación nativa profunda: subagentes spawn/fork con KV-cache reuse, workflow, ralph, goals multi-ronda.
- Superficies múltiples sobre el mismo runtime: web, CLI, headless, ACP, SDK JSON-RPC, Python wheel.
- Seguridad fail-closed con ejecución confinada por SO (bwrap/Landlock/Seatbelt) y approval auditado.

**Oportunidades**
- Único agente GA-quality con arquitectura "everything is a plugin" publicada (arXiv 2608.25512) — liderazgo académico/industrial en composición de agentes.
- Puentes de hooks a Claude Code/Codex ya incluidos: migración de ecosistemas existentes.
- Webhooks + sesiones web + scheduler: posicionamiento como "agent platform" autoservible, no solo CLI.
- MCP como fila nativa: integración con el estándar que ya consolidan los competidores.

**Debilidades**
- Developer preview: APIs de composición movibles, versión 0.1.5-rc.3.
- Ecosistema de plugins/markeplace incipiente; sin comunidad comparable a la de Claude Code.
- Documentación densa y mayormente en formato referencia; curva de perfiles/patches/realms.
- Dependencias de funciones clave en claves DeepSeek (web search oficial) con fallo visible sin configuración (auto-evidenciado en esta investigación).
- Web UI menos pulida que productos con años de UI (Cursor) o backing de big-tech (Gemini CLI).
- Sandbox de shell sin cobertura de red (declarado).

**Amenazas**
- Claude Agent SDK y Codex SDK consolidándose como estándares de facto de integración.
- Cursor absorbiendo el mercado de IDE-agent con distribución preinstalada y precio agresivo.
- Cambios de licencia/TOS de proveedores de API (riesgo de BYOK en general).
- Fragmentación del estándar MCP si los grandes actores lo extienden privativamente.

### Conclusiones (Fase 4)

1. dsh compite en la intersección **MIT + agnosticismo total + composición declarativa** donde solo OpenHands/Aider se acercan, pero con arquitectura de runtime más explícita y superficie web+SDK+ACP más amplia.
2. Su desventaja no es técnica sino de **madurez de ecosistema y producto** (preview, sin marketplace poblado).
3. La evidencia más fuerte del diferenciador "agnosticismo": el propio deployment de producción de esta sesión no usa un modelo DeepSeek.

## FASE 5: ECOSISTEMA DE PLUGINS Y MCP

### Resultados de Introspección

La gestión de plugins es **pnpm real en el directorio del perfil** (forwarding, no un registro propio):

```bash
$ dsh plugin --profile web add <package>     # pnpm add en ~/.dsh/profiles/web
$ dsh plugin --profile web list              # pnpm list
```

Bundles se resuelven primero desde la instalación dsh (`dsh-base`, `dsh-web-app`, `dsh-headless`, `dsh-sdk-app`, `dsh-sdk-minimal`, `dsh-acp-app`) y después del `node_modules` del perfil (donde pnpm instala plugins out-of-tree). Semántica clave: **un patch reemplaza el config completo de la fila (no merge)**.

### Análisis Técnico — MCP (dsh-mcp-client)

Hallazgo que corrige la intuición: **no existe una clave mágica `mcpServers`** — cada servidor MCP es una **fila Cordis más**:

```yaml
# cordis.patch.yml del perfil (o overlay --patch)
- name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: memory
    transport: stdio            # o streamable-http
    command: npx
    args: ['-y', '@modelcontextprotocol/server-memory']
    env: { MEMORY_DIR: /data/memory }
    # HTTP: url: https://… , headers: {…}
```

- **Superficie expuesta al modelo:** herramientas `mcp__<serverName>__<tool>` dentro del catálogo normal del agente.
- **Afinación:** `toolCallTimeoutMs` (default 60000), reconexión exponencial 500 ms→30 s, máx. 10 intentos.
- **Env scrubbing:** elimina variables que casen `/KEY|PASSWORD|SECRET|TOKEN/i` y cualquier `DSH_*` antes de mergear el `env` del servidor — el servidor MCP no hereda secretos del harness por accidente.
- **Limitaciones declaradas:** solo **Tools** (sin Resources/Prompts), timeouts heredados del SDK MCP, imágenes OK, audio/recursos solo diagnóstico.

### Skills (sistema nativo de "plugins de prompt")

Formato: directorio `<name>/SKILL.md` (o `<name>.md`) a un nivel, frontmatter con `name`/`description` requeridos + `whenToUse`, `metadata`, `disable-model-invocation`, `user-invocable`. Registro `ctx.skills` con providers (list/get) e invocation policy (`modelInvocable`/`userInvocable`). **6 raíces priorizadas** (menor rank gana): `.dsh/skills`(100) → `.agents/skills`(200) → `customSkillDirs` del preset(300) → `$DSH_HOME/skills`(400) → `~/.agents/skills`(500) → bundled(600). Project root = ancestro `.git` más cercano. La tool `skill` carga el catálogo de la sesión; el preset `cordis` demuestra `customSkillDirs` apuntando a `skills/` dentro de su propio directorio.

### Guía paso a paso: crear un plugin básico

```bash
# 1. Crear el paquete (un plugin Cordis es un paquete npm con una fila)
mkdir dsh-plugin-hello && cd dsh-plugin-hello
cat > package.json <<'JSON'
{ "name": "dsh-plugin-hello", "version": "0.1.0",
  "main": "index.js",
  "dsh": { "cordis": [ { "id": "hello", "name": "./index.js" } ] } }
JSON

# 2. La fila: un servicio Cordis mínimo
cat > index.js <<'JS'
module.exports = (ctx, config) => {
  ctx.tools?.register?.({ /* tool schema + handler */ })
  return () => { /* dispose */ }
}
JS

# 3. Instalarlo SOLO en el perfil deseado
dsh plugin --profile web add ./dsh-plugin-hello

# 4. Verificar el árbol compuesto sin bootear
dsh --profile web --dump-config | grep -A3 hello
```

Alternativa sin código — **preset propio** (la vía que documenta el preset `cordis`):

```bash
mkdir -p ~/.dsh/.agent-presets/reviewer
cp -r <install>/agent-presets/standard/* ~/.dsh/.agent-presets/reviewer/
# editar agent.cordis.yml: p.ej. quitar tool-bash, añadir tool-web config distinto
```

### Superficies de integración adicionales (evidencia en paquetes)

| Superficie | Qué es | Modo de uso |
|---|---|---|
| **ACP** (`dsh-acp`, `dsh-acp-app`) | Servidor **Agent Client Protocol v1** sobre JSON-RPC stdio: `initialize`, `authenticate` (no-op), `session/new|list|resume|close`, `set_config_option` (model, reasoning_effort), `session/prompt`, `cancel`, `session/update`, `request_permission` | `dsh --profile acp` — clientes de editores/automatización; MCP montable por sesión; limitaciones: 1 workspace, imágenes raster only, sin session/load/fork/delete |
| **SDK** (`dsh-sdk-app`, `dsh-sdk-protocol`, `dsh-sdk-jsonrpc-server`) | Wire JSON-RPC stdio newline-delimited, identidad `deepseek-harness-sdk-runtime`; `session/prompt` → `{messageId}` + stream `session.event`/`session.status` | `dsh --profile sdk`; apps propias en cualquier lenguaje |
| **sdk-minimal** | Árbol Cordis **standalone** (sin dsh-base): 1 shell persistente, JSONL sin comprimir, danger-full-access | `dsh --profile sdk-minimal` — embedding mínimo |
| **Webhooks** (`dsh-webhook`, `dsh-webhook-github`) | `ctx.webhookRuntime` register(rule)/dispatch → crea **nuevas Sessions** en Web Workspaces (fire-and-forget, sin dedup/retry). Adapter GitHub: 1 ruta HTTP exacta, `X-Hub-Signature-256` HMAC, 202/400/401/405/413/415/503 | Overlay opt-in; guía recomienda puerto dedicado `127.0.0.1:3081/github` tras reverse proxy TLS |
| **Hooks bridges** (`dsh-hooks-claude-code`, `dsh-hooks-codex`, `dsh-hook-protocol`) | Compat-adapters que ejecutan `hooks.json` existentes mapeando a extension points Cordis (`agent/pre-step`, `tools/pre-execute`, …). Claude Code: 7/30 eventos; Codex: 5 | `configPath` único por proceso, handlers shell, timeout default 600000 ms |
| **http-proxy** | Librería (no plugin) con **una política proxy por proceso** para `fetch` | Lee `http_proxy/https_proxy/no_proxy/all_proxy` del snapshot del launcher (`$DSH_HOME/.env` permitido; `.env` de proyecto **prohibido** para estas vars); loopback siempre bypass; sin SOCKS/PAC |
| **Schedule** (`dsh-schedule`) | Recordatorios **session-local** durables (eventos `schedule/change` en el session log) | Overlay opt-in; tools `schedule_create/list/delete`; one-shot o repetitivos ≥5 min; se entregan como mensaje follow-up cuando el agente está idle |

**Variables `DSH_*` documentadas** (selección): `DSH_HOME`, `DSH_AGENTS_HOME`, `DSH_TOOLS_MODE` (opt-in PTC), `DSH_CONTEXT_WINDOW`, `DSH_SYSTEM_PROMPT`, `DSH_MAX_TOKENS_AS_SUCCESS`, `DSH_TELEMETRY_DISABLED`/`DSH_TELEMETRY_MODE=DISABLED`, `DSH_WEB_URL`, `DEEPSEEK_API_KEY`, más proxy vars. Internas observadas en vivo: `DSH_SESSION_ID`, `DSH_SHELL`, `DSH_SUBPROCESS_RUNNER`, `DSH_WEB_FETCH_PROVIDER`, `DSH_WEB_SEARCH_PROVIDER`, `DSH_SNAPSHOT`.

**Nota de packaging:** los `config/examples/` que el README menciona (GitHub review, schedule, memory MCP) **no se publican en npm** (`files: ["lib/*.js"]`); las guías de setup viven en `docs/user/guide/` del repo.

### Conclusiones (Fase 5)

1. La extensibilidad tiene **tres escalones**: (a) patch YAML sin código, (b) preset de agente (directorio copiable), (c) paquete npm con filas Cordis.
2. MCP es ciudadano de primera clase pero ** Cordis-native**: un servidor = una fila, con scrubbing de secretos y naming `mcp__server__tool`.
3. Las superficies ACP/SDK hacen de dsh un **runtime embebible**, no solo una app: el mismo árbol de plugins sirve a la GUI web, a editores (ACP) y a programas (JSON-RPC).

---

## FASE 6: MEJORES PRÁCTICAS Y LIMITACIONES — 6.1 CHECKLIST DE SEGURIDAD Y MODELO DE AMENAZAS

*(Las limitaciones conocidas, workarounds y casos de uso avanzados completan esta fase en la sección 6.2, al final del documento.)*

### Resultados de Introspección

Evidencia directa de los ejecutores del host plane:

**`dsh-bash-sandbox`** (confinamiento por comando, no por proceso):
- Runners reales: **bubblewrap** (Linux), **Landlock** (Linux), **Seatbelt** (macOS).
- Semántica de modos (tabla del README, verificada):

| Modo | Efecto |
|---|---|
| `read-only` | Sin escrituras en ningún sitio; solo `/dev/null` escribible (para que `>/dev/null` siga funcionando) |
| `workspace-write` | Escrituras solo bajo el workspace root + `/tmp` (efímero bajo bwrap; `/private/tmp` + tempdir del usuario bajo Seatbelt) |
| `danger-full-access` | Sin confinamiento; el provider nunca se consulta; resultado lleva `sandbox: { mode, denied: false }` |

- **Fail-closed**: si ningún runner puede aplicar el modo, el comando falla con `SANDBOX_UNAVAILABLE` — *nunca* corre sin confinar.
- **Deny-only at the seam**: el ejecutor jamás concede permiso; la escalación la maneja la capa de tool (una sola re-intento del comando exacto con el modo más estrecho que baste + justificación, sujeto a approval).
- Red y visibilidad de procesos **quedan fuera** de las garantías (declarado honestamente).

**`dsh-fs-sandbox`**: mutaciones confinadas por llamada; `read-only` rechaza toda mutación con `FS_SANDBOX_DENIED`; `workspace-write` exige que el target canonicalice bajo el workspace o temp; las lecturas quedan intactas; la pista de escalación se da en el mismo turno.

**`dsh-user-approval`**: seam de aprobación one-shot y channel-neutral. `ask` → answerers (UI humana o máquina); `never` → rechazo determinista antes de despachar (postura estricta de CI); sin answerer → `unavailable` = **fail closed**. Requiere turno abierto; abortar = `cancelled`; doble auditoría (append) o el decisión no se devuelve. La política efectiva: override de sesión > default del deployment. Todo queda en el audit log de la sesión; el modelo ve solo el outcome.

### Checklist de seguridad para producción

1. **Default `read-only` o `workspace-write`** en el deployment; `danger-full-access` solo interactivo y consciente (en esta sesión el usuario lo activó a las 14:20 del log — el cambio quedó auditado como eventos `permission/preset` + `sandbox/mode` + `approval/policy`).
2. **Approval `ask`** en cualquier entorno con datos sensibles alcanzables; `never` reservado para CI efímera/containers desechables.
3. **Claves vía `apiKeyEnv`**, nunca en YAML; `~/.dsh/.credentials.yaml` con chmod 600; sesiones y storages ya nacen con `drwx------`.
4. **Preset `cordis` = shell access**: montarlo solo para usuarios de confianza; `cordis_mount` evalúa JavaScript del modelo contra el runtime vivo y la composición escrita se monta para otras sesiones.
5. **Subagentes heredan la política**: la delegación no eleva privilegios (`delegationDepth` queda en el session header; los providers codex/claude-code viajan **disabled** por defecto en el preset).
6. **Webhooks** (`dsh-webhook`, `dsh-webhook-github`): usar los overlays opt-in de `config/examples/` con secretos por env-var y verificación de firma.
7. **Telemetría**: `DSH_TELEMETRY_MODE` (default `FEEDBACK_ONLY`) apunta a OTLP; revisar antes de despliegues privados.
8. **MCP**: cada servidor MCP corre con la autoridad del proceso host — correr stdio servers con su propio sandbox (ver Fase 5).
9. **Auditoría forense**: `session.v3.jsonl.zstd` es append-only con `session.lock`; conservarlo como fuente de verdad de políticas y comandos.

---

## FASE 6 (continuación, 6.2): LIMITACIONES, WORKAROUNDS Y CASOS DE USO AVANZADOS

### Limitaciones conocidas (declaradas en los propios READMEs, v0.1.5-rc.3)

| # | Limitación | Workaround |
|---|---|---|
| 1 | **El sandbox de bash no cubre red ni visibilidad de procesos** (declarado) | Asumir que cualquier comando puede hablar por red; usar entornos efímeros para lo sensible |
| 2 | **MCP client: solo Tools** — sin Resources/Prompts del protocolo | Exponer lo que falte como tools adicionales en el servidor |
| 3 | **Web search provider oficial requiere `DEEPSEEK_API_KEY`** | Configurar otro provider de fetch/search vía las filas `web`/`web-search-*` |
| 4 | **Hooks bridges parciales**: Claude Code 7/30 eventos, Codex 5; solo handlers shell; `transcript_path` vacío | Mantener hooks simples y stateless |
| 5 | **ACP limitado**: 1 workspace, imágenes raster only, sin session/load/fork/delete | Usar el perfil web/sdk para esas capacidades |
| 6 | **Webhook dispatch fire-and-forget**: sin dedup ni retry | Idempotencia en el lado del agente; re-procesar desde el session log |
| 7 | **Preset `minimal` sin compactación**: el contexto crece indefinidamente | Sesiones cortas; o usar standard con pruner |
| 8 | **`tui` no existe como bundle en 0.1.5-rc.3** (aparece en el help como ejemplo) | Los perfiles shipped reales: web, headless, sdk, sdk-minimal, acp |
| 9 | **Patches reemplazan config completo de la fila (no merge)** | Copiar el bloque completo del dump al `cordis.patch.yml` antes de editarlo |
| 10 | **Versión RC**: 0.1.5-rc.3 — APIs de composición aún movibles | Fijar versión en producción; revisar release notes al actualizar |

### Casos de uso avanzados

**1. Orquestación multi-agente con `workflow` (patrón real usado en esta misión):**

```js
// workflow(args: {files: [...]}) — script puro: sin fs/net; los AGENTES hacen el trabajo
const results = await pipeline(args.files,
  async (file) => ({
    file,
    issues: await agent(`Audita ${file} buscando X; devuelve JSON estructurado`, {
      schema: {type:'object', properties:{issues:{type:'array'}}, required:['issues']},
      label: `audit:${file}`
    })
  }),
  // verificación adversarial en fase separada
  async (prev, file) => prev && await agent(`Verifica estos hallazgos de ${file}: ${JSON.stringify(prev.issues)}`)
);
return results.filter(Boolean);
```

**2. Ralph loop para convergencia iterativa** — objetivo inmutable, cada ronda un agente fresco, el workspace compartido como memoria duradera, solo un report acotado cruza rondas. Ideal para refactors con verificación repetida (`maxRounds` default 64).

**3. Delegación por proveedor externo** — el preset standard incluye filas `tool-subagent-codex` y `tool-subagent-claude-code` (disabled): instalar el bundle correspondiente en el perfil, copiar el preset, quitar `disabled` → el agente puede delegar a Codex/Claude Code como subordinados (`maxDepth: provider-managed`).

**4. CI headless one-shot:**

```bash
dsh --profile headless "run the tests and report failures"   # sesión fresca, imprime la respuesta final, exit
# con approval never + sandbox read-only vía preset de deployment
```

**5. Programación por lotes vía SDK (cualquier lenguaje):**

```jsonc
// JSON-RPC stdio → dsh --profile sdk
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"provider":"k2p6","model":"k2p6"}}
{"jsonrpc":"2.0","id":2,"method":"session/prompt","params":{"text":"resume build"}}
// → stream: session.event (tokens), session.status (turn lifecycle)
```

**6. Webhook de revisión de PR (GitHub)** — overlay: `dsh-webhook-github` con `secretEnv`, ruta dedicada `127.0.0.1:3081/github` tras reverse proxy TLS → cada delivery crea una sesión del agente en el web workspace.

### Optimización de rendimiento y costo

- **Compacación preventiva**: el pruner acota resultados de tool >8192 chars (head 4096/tail 1024); spill externaliza >50 KiB inline.
- **Preset `ptc`**: un `run_code` sustituye N round-trips → menos tokens de sistema por paso.
- **`subagent_fork`** hereda historial y modelo del padre: reutilización de KV cache (fork omite selección de modelo a propósito).
- **`maxParallelToolCalls: 10`** (default) para herramientas paralelas-seguras; serializar lo exclusivo.
- **Telemetría desactivable**: `DSH_TELEMETRY_MODE=DISABLED`.
- **repeat-tool-reminder** (umbrales 3/5/8) corta bucles de tool-calls repetidos antes de quemar presupuesto.

### Conclusiones (Fase 6)

1. Las limitaciones están **declaradas en los READMEs de cada paquete** — la documentación es parte del producto, no un afterthought.
2. Los casos avanzados no requieren código del harness: se componen con presets, overlays y los perfiles embebibles (headless/sdk/acp).
3. El modelo de costo favorece composición declarativa (ptc, fork, workflow) sobre chat multi-turno largo.

---

## APÉNDICE A: TRAZABILIDAD DE LA INVESTIGACIÓN

Comandos y lecturas ejecutados en vivo durante esta sesión (todos reproducibles):

```bash
dsh --version                                 # 0.1.5-rc.3
dsh --help                                    # gramática del launcher
dsh --profile web --dump-config               # 539 líneas de árbol compuesto (guardado en /tmp/dsh-web-config.yml)
env | grep -i dsh                             # DSH_HOME, DSH_SESSION_ID, DSH_WEB_URL, DSH_SHELL
ls ~/.dsh ~/.dsh/profiles ~/.dsh/sessions ~/.dsh/storages
cat ~/.dsh/profiles/web/package.json          # bundles del perfil activo
cat ~/.dsh/settings.yaml                      # provider k2p6 (Kimi) vía anthropic-messages — sanitizado
zstd -dc …/session-de30e99f…/session.v3.jsonl.zstd | head   # eventos reales de política de la sesión
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3080/   # 401 (auth por URL del boot)
ls /home/atom/.npm/_npx/1e7f6d9597241db0/node_modules/@deepseek-ai/ | wc -l   # 241 paquetes
cat node_modules/@deepseek-ai/dsh-agent-presets/presets/{standard,ptc,minimal,cordis}/{preset.yml,agent.cordis.yml}
```

Lecturas de código fuente (selección): README de `dsh`, `dsh-agent-loop`, `dsh-sandbox-policy`, `dsh-user-approval`, `dsh-bash-sandbox`, `dsh-fs-sandbox`, `dsh-mcp-client`, `dsh-skill*`, `dsh-webhook*`, `dsh-hooks-*`, `dsh-acp*`, `dsh-sdk-*`, `dsh-http-proxy`, `dsh-schedule`, y package.json del monorepo.

Delegaciones paralelas (investigación asistida por subagentes del propio harness):
- Catálogo de herramientas desde los paquetes `dsh-tool-*`.
- Ecosistema MCP/plugins/skills/webhooks/ACP/SDK → `deepseek-harness-ecosystem-report.md`.
- Research web comparativo (Fase 4) con fuentes citadas.

## APÉNDICE B: HONESTIDAD SOBRE LO NO ACCESIBLE

- **No se expone** el contenido de `~/.dsh/.credentials.yaml` ni de `K2P6_API_KEY` (por diseño).
- El **webserver** rechazó la introspección HTTP sin el token de boot (401) — la evidencia del plano web proviene del código y del dump-config, no de la API en caliente.
- Los **`config/examples/`** no se publican en npm; su documentación teórica proviene de los READMEs que los referencian.
- La **telemetría** efectivamente activa depende de `DSH_TELEMETRY_MODE`; el default del bundle es `FEEDBACK_ONLY` con OTLP a DeepSeek.

---
