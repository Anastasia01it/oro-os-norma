# Ecosistema de plugins, skills, webhooks y MCP de DeepSeek Harness (DSH)

> Investigación sobre el checkout npm en `/home/atom/.npm/_npx/1e7f6d9597241db0/node_modules/@deepseek-ai/`
> (versión `0.1.5-rc.3`, repo: `github.com/deepseek-ai/deepseek-harness`). Toda afirmación cita la ruta de evidencia.

## 0. Arquitectura general: todo es un perfil Cordis

`dsh` es el único lanzador soportado. Un **perfil** es una pila ordenada de capas de *patch* de *bundles* de plugins, bajo overrides del usuario (`@deepseek-ai/dsh/README.md`). El sistema de plugins subyacente es **Cordis** (`@deepseek-ai/cordis` 4.0.2 + plugins `cordis-plugin-loader`, `cordis-plugin-hmr`, `cordis-plugin-include`, `cordis-plugin-timer`, `cordis-plugin-group`).

Composición del árbol (`dsh/README.md` líneas 37–44):
1. Raíz vacía.
2. El patch de cada bundle en el orden de `dsh.profile.bundles`.
3. El `cordis.patch.yml` del perfil, luego el `cordis.patch.yml` a nivel home (`$DSH_HOME/cordis.patch.yml`).
4. Overlays `--patch <path>` (repetibles, en orden).

Bundles preinstalados que resuelven desde la instalación dsh: `dsh-base`, `dsh-web-app`, `dsh-headless`, `dsh-sdk-app`, `dsh-sdk-minimal`, `dsh-acp-app`. Los plugins out-of-tree se instalan con pnpm en el `node_modules` del perfil (`dsh plugin --profile <name> add <pkg>`).

Un directorio de perfil contiene:
- `package.json` con el manifiesto `dsh.profile` (`bundles` ordenados + `patchReload: live|startup`).
- `cordis.patch.yml` (capa de patch del usuario).

Reglas clave: cada patch **reemplaza el `config` completo** de la fila objetivo (no merge); última escritura gana por fila; `desktop` es nombre reservado (perfil Electron).

---

## 1. `@deepseek-ai/dsh-mcp-client` — puente MCP cliente

**Evidencia:** `dsh-mcp-client/README.md` (212 líneas), `dsh-mcp-client/lib/index.js`, `dsh-mcp-client/package.json` (depende de `@modelcontextprotocol/sdk ^1.12.0`).

### Qué hace
Registra herramientas de servidores MCP externos como herramientas nativas del agente. Configuración: **una entrada por servidor** en una lista de plugins Cordis (no existe una clave mágica `mcpServers` — cada servidor es una fila `- id / name / config`). Herramientas expuestas como `mcp__<serverName>__<tool>`, p. ej. `mcp__github__create_issue` (misma convención que Claude Code/Codex).

### Transports
- `stdio` — `command`, `args`, `env`, `cwd` (servidor local como proceso).
- `streamable-http` — `url`, `headers` (servicio remoto). No SSE clásico ni ACP-transport; solo stdio y Streamable HTTP (`dsh-acp/README.md` lo confirma para ACP).

### Formato de config (ejemplo documentado, README líneas 34–53)
```yaml
- id: mcp-github
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: github
    transport: stdio
    command: npx
    args: ['-y', '@modelcontextprotocol/server-github']
    env:
      GITHUB_TOKEN: !!js process.env.GITHUB_TOKEN

- id: mcp-web
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: web
    transport: streamable-http
    url: http://localhost:3000/mcp
    headers:
      Authorization: !!js '`Bearer ${process.env.MCP_TOKEN}`'
```

| Campo | Default | Significado |
|---|---|---|
| `transport` | requerido | `stdio` o `streamable-http` |
| `serverName` | requerido | Namespace `[A-Za-z0-9_-]{1,32}`, único por scope de registro |
| `command`/`args`/`env`/`cwd` | — | stdio |
| `url`/`headers` | — | streamable-http |
| `toolCallTimeoutMs` | 60000 | Timeout por `tools/call` |
| `failOnStartupError` | false | Abortar activación si falla sync inicial |
| `reconnect.enabled` | true | Reconexión automática |
| `reconnect.initialDelayMs` | 500 | Backoff exponencial ×2 |
| `reconnect.maxDelayMs` | 30000 | Techo de backoff |
| `reconnect.maxAttempts` | 10 | Tras 10 fallos seguidos, desregistra herramientas |

### Semántica de registro y naming
- Identidad estable `(serverName, rawName)`; el nombre remoto `serverInfo.name` es **no confiable** y nunca se usa (`lib/index.js` función `publicToolName()`; si hay normalización de caracteres se añade hash SHA-256 de 12 hex).
- `tools/call` siempre recibe el nombre raw; el nombre público nunca viaja al servidor.
- Sync atómico "todo o nada": fallo de fetch mantiene la generación anterior; conflicto de registro hace rollback de toda la generación. Escucha `notifications/tools/list_changed`.
- Env scrubbing en stdio: se eliminan variables ambientales que casen `/KEY|PASSWORD|SECRET|TOKEN/i` y `DSH_*` antes de aplicar `env` configurado.
- Imágenes PNG/JPEG/WebP/GIF soportadas si el modelo acepta imágenes; audio y recursos embebidos quedan como diagnóstico de texto.

### Limitaciones documentadas
- Solo se puentean **herramientas**; Resources y Prompts MCP no tienen consumidor en el harness.
- Timeouts de conexión/discovery heredados del SDK MCP (60 s por request; sin timeout propio).
- Reconnect del supervisor solo para cierre de transporte (stdio); HTTP falla por request vía SDK.
- Herramientas MCP que requieren extensión *task-based execution* se rechazan en call time.
- Esquemas de salida fuera del subset soportado no se validan (fallback `JsonValue`).

---

## 2. `@deepseek-ai/dsh-skill` + `@deepseek-ai/dsh-skill-filesystem` — sistema de skills

**Evidencia:** `dsh-skill/README.md`, `dsh-skill-filesystem/README.md`.

### dsh-skill (registro)
- Servicio `ctx.skills`: catálogo **fusionado** de skills de cualquier fuente (providers) + skills embebidas (`ctx.skills.register(...)`).
- Providers: objeto en proceso con `list()` (candidatos) y `get()` (cuerpo); se registran con `ctx.skills.registerProvider(...)`; `runtime` es nombre reservado.
- Resolución de duplicados: first-wins por capa (host global → capa del preset del agente), dentro de la capa por rank, orden de registro del provider y orden local.
- **Invocation policy** por skill: `modelInvocable` / `userInvocable` (4 combinaciones; decide si aparece en catálogos del modelo y/o comandos humanos).
- Config: `collectCacheMaxEntries` (default 128). Sin TTL: invalidación solo por el provider (`invalidate()`), evento `skills/change`.
- El consumidor model-facing es `dsh-tool-skill` (herramienta `skill`); este paquete no incluye contenido.

### dsh-skill-filesystem (provider local)
- Formato de skill: **directorio** `<name>/SKILL.md` o **archivo plano** `<name>.md` en el top-level de una raíz escaneada (sin `**/SKILL.md` anidados).
- Frontmatter YAML: `name` (kebab-case) y `description` requeridos; opcionales `whenToUse`, `metadata`, `disable-model-invocation`, `user-invocable` (booleans estrictos: true/false/yes/no/on/off/1/0; un valor inválido **descarta el skill con warning**).
- Raíces por defecto en orden de prioridad:

| Rank | Fuente | Path |
|---|---|---|
| 100 | project-dsh | `<projectRoot>/.dsh/skills` |
| 200 | project-agents | `<projectRoot>/.agents/skills` |
| 300 | custom | `Config.customSkillDirs` |
| 400 | user-dsh | `<dshHome>/skills` |
| 500 | user-agents | `<agentsHome>/skills` |
| 600 | bundled | `bundledSkillDir` (opcional) |

- `projectRoot` = ancestro más cercano con `.git` (sin `.git`, cwd). El usuario DSH salta `.system`.
- Config: `providerName` (default `filesystem`), `includeDefaultRoots` (true), `dshHome` (`$DSH_HOME` o `~/.dsh`), `agentsHome` (`$DSH_AGENTS_HOME` o `~/.agents`), `customSkillDirs` [], `watch` (true, Chokidar depth 1), `watch*` (polling etc.), `bundledSkillDir`.
- Los tools first-party `write`/`edit` invalidan el provider vía evento `fs/observed`.
- Limitaciones: descubrimiento a 1 nivel; sin protocolo de revisión de cuerpo (cada load relee el archivo); entradas malformadas desaparecen silenciosamente para el modelo; project scope atado a `.git`.

---

## 3. `@deepseek-ai/dsh-webhook` + `@deepseek-ai/dsh-webhook-github`

**Evidencia:** `dsh-webhook/README.md`, `dsh-webhook-github/README.md`.

### dsh-webhook (runtime)
- Expone `ctx.webhookRuntime` en el plano Host Web: `register(rule)` / `dispatch(delivery)`.
- `WebhookRule<K>`: `id`, `kind` (provider), `run(delivery, signal)` → `null` o un `WebhookSessionRequest`.
- `WebhookSessionRequest` requiere `workspacePath`, `title`, `prompt`, `agentPreset`, `permissionPreset`; opcional `model` (ruta provider/model + cap de tokens). El runtime crea un Workspace canónico, monta el preset del agente, aplica permisos/título/prompt y hace `Agent.followup()` con `source.kind: "webhook"`.
- Fire-and-forget en proceso: sin cola, replay, dedup ni resultado de completitud. Entrega `VerifiedWebhookDelivery` con JSON lossless congelado (snapshot).

### dsh-webhook-github (adapter firmado)
- Registra **una ruta HTTP exacta** en `ctx.webServer`. Config requerida: `source` (etiqueta, p. ej. `primary-github`), `path` (pathname exacto), `secretEnv` (referencia de credencial, resuelta por request — rotación sin reload), `maxBodyBytes`.
- Contrato HTTP: solo `POST application/json`; valida `X-Hub-Signature-256` (HMAC antes de parsear JSON), `X-GitHub-Delivery`, `X-GitHub-Event`. Respuestas: 202 despachado / 400 / 401 firma / 405 / 413 / 415 / 503. Nunca logea secreto ni payload.
- Composición con puerto dedicado: montar otro `dsh-host-webserver` + adapter dentro de un grupo que aísle solo `webServer`; la guía usa `127.0.0.1:3081/github` detrás de reverse proxy TLS mientras la UI va en 3080.
- Limitaciones: sin TLS propio (loopback detrás de proxy), validación genérica de payload (las reglas validan campos del evento), sin ack de trabajo downstream.

---

## 4. `@deepseek-ai/dsh-hooks-claude-code` y `@deepseek-ai/dsh-hooks-codex` — puentes de hooks

**Evidencia:** `dsh-hooks-claude-code/README.md` (194 líneas), `dsh-hooks-codex/README.md`, `dsh-hook-protocol/package.json` ("Shared Claude Code / Codex hook wire protocol: matcher engine, stdin/exit-code/stdout codec, multi-hook merge, hook/* session events").

### Concepto común
Compat adapters: ejecutan los command-hooks de una config existente de Claude Code / Codex durante los runs del agente, mapeando a extension points nativos (`agent/session-start`, `agent/pre-step`, `tools/pre-execute`, `tools/post-execute`, `agent/turn-stopping`, `subagent/start`, `subagent/end`). Los hooks corren en el workspace de la sesión; fallos se logean y el agente continúa; runs en serie en orden de config; fold de decisión order-independent (`deny > ask > allow`).

### Claude Code (`configPath` → `hooks.json` o settings con clave `hooks`)
Config: `configPath` (requerido), `pluginRoot` (sustituye `${CLAUDE_PLUGIN_ROOT}`), `projectDir` (sustituye `${CLAUDE_PROJECT_DIR}` y env var), `defaultTimeoutMs` 600000, `stderrSummaryMaxChars` 500.
Eventos soportados (7): `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStart`, `SubagentStop`.
Limitaciones: 23 de 30 eventos no soportados; `PreToolUse` sin `allow`/`defer`/`updatedInput`; `transcript_path` siempre `''`; solo handlers shell (sin `http`, `mcp_tool`, `prompt`, `agent`); un solo configPath a nivel proceso (sin discovery por capas ni reload); ejecución serie en vez de paralela.

### Codex (`configPath` → `hooks.json`)
Config: `configPath` (requerido), `model` (string estampado en payloads), `defaultTimeoutMs` 600000, `stderrSummaryMaxChars` 500.
Eventos soportados (5): `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`.
Limitaciones: 5 de 10 eventos no soportados (`PermissionRequest`, `PreCompact`, `PostCompact`, `SubagentStart`, `SubagentStop`); sin pre-tool approval; tool arguments reducidos a `tool_input: { command }`; `transcript_path` siempre `null`; matchers regex no anclados; sin capas de config de Codex.

---

## 5. `@deepseek-ai/dsh-http-proxy` — proxy HTTP de salida

**Evidencia:** `dsh-http-proxy/README.md` (126 líneas).

- **No es un plugin**: es una librería que el launcher instala antes de cargar el primer plugin. Una política de proxy por proceso para todo `fetch` de Node (LLM, web-search, MCP HTTP).
- Lee `http_proxy`, `https_proxy`, `no_proxy`, `all_proxy` (minúscula primero, mayúscula fallback; `ALL_PROXY` respalda ambos esquemas; HTTPS cae a proxy HTTP al final). Valores: snapshot del launcher — exportadas primero, luego `$DSH_HOME/.env`. El `.env` del proyecto **no** puede llevar estas variables (el launcher se niega a arrancar).
- Loopback siempre en bypass (`localhost`, `127.0.0.0/8`, `::1`, `0.0.0.0`, IPv4-mapped).
- Helpers públicos: `proxyRouteFor(url)`, `proxyEnvironmentForChild()`, `clearedProxyEnv()`, `proxyForUrl()`.
- Sin SOCKS/PAC ni detección de proxy del SO; sin CA personalizada (necesita `NODE_EXTRA_CA_CERTS` previo al launch); telemetría OTLP va directa por diseño; workers de código model-authored (`code-runtime`, `workflow`) no reciben proxy.

---

## 6. `@deepseek-ai/dsh-schedule` — recordatorios session-local

**Evidencia:** `dsh-schedule/README.md` (233 líneas).

- Herramientas del modelo: `schedule_create`, `schedule_list`, `schedule_delete`. Recordatorios one-shot (delay o tiempo absoluto con offset RFC 3339 o zona explícita) o repetitivos de intervalo fijo (mínimo 5 min, anclados a la creación).
- Activo: se entregan como mensajes follow-up ordinarios en la **misma sesión** cuando el agente está idle; no hay email/SMS/push. Sesión cerrada = recordatorio queda overdue hasta resumir.
- Estado durable: eventos `schedule/change` v1 en el log de sesión (replay estricto, decodificador rechaza versiones/desconocidos). Forks no heredan recordatorios.
- Habilitación: overlay opcional; `dsh web --patch apps/cli/config/examples/schedule/cordis.yml` (los ejemplos no se publican en npm; el paquete `dsh` solo empaqueta `lib/*.js`).
- El framing al modelo marca el contenido como *untrusted reminder content*.
- Limitaciones: solo intervalos fijos (sin reglas de calendario/cron), latest-only catch-up, sin retry privado, load-order boundary (no adopta agents ya vivos), catálogo Web de solo lectura.

---

## 7. `@deepseek-ai/dsh-acp` + `@deepseek-ai/dsh-acp-app` — Agent Client Protocol

**Evidencia:** `dsh-acp/README.md` (182 líneas), `dsh-acp-app/README.md`, `dsh-acp-app/cordis.patch.yml`.

### dsh-acp
- Servidor **ACP v1** (agentclientprotocol.com) sobre JSON-RPC stdio, para clientes de confianza: out-of-process subagents, test runners, controladores script. Automatización solamente — sin datos de presentación DSH ni UI interactiva.
- Arranque: `dsh --profile acp`. Config: `provider`, `model` (ambos opcionales), `sessionListPageSize` (100).
- Métodos: `initialize` (anuncia ACP v1 + `session/list`/`resume`/`close` + MCP Streamable HTTP), `authenticate` (éxito inmediato), `session/new` (con `cwd` absoluto y declaraciones MCP stdio/HTTP validadas), `session/list`, `session/resume` (sin replay de historia), `session/close`, `session/set_config_option` (`model`, `reasoning_effort`), `session/prompt` (uno por sesión), `session/cancel`, `$/cancel_request`, `session/update`, `session/request_permission`.
- Cliente de referencia: `dsh-subagent-acp` (delegación out-of-process).
- Limitaciones: un solo workspace primario (sin additional directories), imágenes raster solo, MCP tools only, sin `session/load`/delete/fork/modes/commands/plans/terminals/fs del cliente/elicitation.

### dsh-acp-app
- Bundle de perfil `acp` sobre `dsh-base`: persona coding-agent, provider de comandos zero-option, arranca `dsh-acp` solo tras aceptar la invocación. La fila shipped crea sesiones con `deepseek-official` / `deepseek-v4-flash`.
- stdout reservado a frames JSON-RPC; EOF de stdin = shutdown acotado; `patchReload: startup`.
- `--help` escribe ayuda y sale sin reclamar stdin/stdout.

**Nota sobre Zed**: ACP es el protocolo que editores como Zed usan; el paquete se presenta como servidor de automatización vía stdio (`dsh --profile acp`), no hay integración Zed específica documentada en el paquete.

---

## 8. SDK: `dsh-sdk-app`, `dsh-sdk-minimal`, `dsh-sdk-jsonrpc-server` (+ `dsh-sdk-protocol`)

**Evidencia:** `dsh-sdk-app/README.md`, `dsh-sdk-minimal/README.md`, `dsh-sdk-jsonrpc-server/README.md`, `dsh-sdk-minimal/cordis.patch.yml`, `dsh-sdk-protocol/package.json`.

### dsh-sdk-jsonrpc-server (plugin de serving)
- Sirve el wire protocol SDK sobre stdio: un agente por `sessionId`, `session/prompt` encola mensajes y devuelve `{ messageId }`, stream de `session.event` + `session.status`. Handshake `initialize` = frontera de readiness (espera al árbol de plugins); identidad de wire `deepseek-harness-sdk-runtime`.
- Config: `maxTokensAsSuccess` (default false; también vía env `DSH_MAX_TOKENS_AS_SUCCESS`). `shutdown` dispone el runtime y sale 0.
- stdout solo frames JSON-RPC (sin loggers stdout en el árbol). No hay close/cancel por sesión ni resultado por prompt.

### dsh-sdk-app (perfil `sdk`)
Bundle sobre `dsh-base`: persona coding-agent, startup provider, servidor JSON-RPC. Herramientas por defecto `read`, `write`, `edit` (sin `str_replace_editor`, que es opt-in por patch).

### dsh-sdk-minimal (perfil `sdk-minimal`)
Árbol Cordis **completo y standalone** (no hereda `dsh-base`): un solo stack de shell persistente (bash en Linux/macOS, pwsh en Windows, timeout 300 s), sesiones JSONL sin comprimir en `$DSH_HOME/sessions`, política `danger-full-access`, sin settings, credenciales gestionadas, telemetría, compaction, fs tools, skills, jobs ni subagents. Credencial vía `DEEPSEEK_API_KEY`; `DSH_CONTEXT_WINDOW` (fallback capacity), `DSH_SYSTEM_PROMPT` (persona). El `initialize` del SDK es la única selección de modelo.

### dsh-sdk-protocol
Protocolo de wire compartido: transporte JSON-RPC stdio newline-delimited + tipos nombrados de requests/results/notifications entre runtime y clientes SDK (lo usan el servidor y los clientes TS/Python).

---

## 9. La CLI `dsh` — instalación, perfiles, plugin command, entorno

**Evidencia:** `dsh/README.md` (56 líneas), `dsh/lib/bin.js` (gramática commander completa), `dsh-base/README.md` (sección "A minimal custom profile"), `dsh-headless/README.md`, `dsh-web-app/README.md`.

### Instalación
Paquete npm `@deepseek-ai/dsh` (bin `dsh` → `lib/bin.js`). El runtime Python empaqueta el mismo comando. Perfiles auto-inicializables en primer uso: `web`, `headless`, `sdk`, `sdk-minimal`, `acp`.

### Entry modes (`lib/bin.js`)
| Comando | Propósito |
|---|---|
| `dsh --profile <name>` | Boot del perfil en `$DSH_HOME/profiles/<name>` |
| `dsh --profile <name> --from-default-profile <template>` | Crear perfil custom desde plantilla shipped y arrancarlo |
| `dsh --profile acp` | Servir clientes de automatización por ACP stdio |
| `dsh --profile headless "job"` | Una sesión fresca persistida, imprime respuesta final, sale |
| `dsh --profile sdk` / `sdk-minimal` | Servir clientes SDK por JSON-RPC stdio |
| `dsh web` | Alias de `--profile web` |
| `dsh plugin --profile <name> <pnpm args>` | Gestión de plugins del perfil (forwarding a pnpm) |

Flags del launcher: `--patch <path>` (repetible), `--dump-config`, `--dump-default-config`, `-V/--version`. Todo token no reconocido pasa a la app del perfil (p. ej. `dsh --profile web --port 8080`). El perfil `desktop` se rechaza.

### Crear plugins/perfiles
- Perfil mínimo sobre el core: `package.json` con `"dsh": { "profile": { "bundles": ["@deepseek-ai/dsh-base"] } }` y `cordis.patch.yml` propio (`dsh-base/README.md` líneas 30–46).
- Añadir bundles: `dsh plugin --profile <name> add <package>` (resolución: instalación dsh primero, luego `node_modules` del perfil).
- Patches en `cordis.patch.yml`: operaciones `insert` con filas `- id / name / config` (ejemplo real: `dsh-sdk-minimal/cordis.patch.yml`, ~60 filas con `disabled: !!js process.platform === 'win32'`). Cada patch reemplaza el config completo de la fila.
- Ejemplo de opt-in (`str_replace_editor`):
```yaml
- insert:
    - id: tool-str-replace-editor
      name: '@deepseek-ai/dsh-tool-str-replace-editor'
      config:
        maxOutputChars: 16000
```

### Perfiles
- **web**: servidor GUI en navegador; `surfaceContext: true` expone `DSH_WEB_URL` a los shells del agente; cada sesión de navegador compone su agente desde presets (`standard` por defecto); presets custom en `$DSH_HOME/.agent-presets`.
- **headless**: one-shot; razonamiento a stderr bajo `dsh: reasoning:`, respuesta final a stdout, exit 0/1; config `task` (requerido).
- **tui**: no aparece como bundle shipped en esta versión (`dsh --profile tui` requiere perfil instalado; los ejemplos del help lo usan como ilustración).
- **acp / sdk / sdk-minimal**: ver secciones 7–8.
- `patchReload: live` observa perfil y home; `startup` aplica una vez (perfiles sdk/acp shipped usan startup).

### Variables de entorno documentadas
| Variable | Semántica (evidencia) |
|---|---|
| `DSH_HOME` | Raíz de config; default `~/.dsh`; precedencia: configurado > env > default (`dsh-home-paths/lib/index.js`) |
| `DSH_AGENTS_HOME` | Raíz de config de agentes compartida; default `~/.agents` (`dsh-skill-filesystem`) |
| `DSH_BUNDLED_SKILL_DIR` | Raíz de skills bundled (rank 600) (`dsh-skill-filesystem`) |
| `DSH_TOOLS_MODE` | Opt-in PTC (programmatic tool calls) mode process-wide (`dsh-headless`, `dsh-web-app`) |
| `DSH_WEB_URL` | URL de la web app expuesta al shell del agente (`dsh-web-app`) |
| `DSH_CONTEXT_WINDOW` | Fallback de context window para modelo fuera del catálogo (`dsh-sdk-minimal`) |
| `DSH_SYSTEM_PROMPT` | Reemplaza la persona default en sdk-minimal |
| `DSH_MAX_TOKENS_AS_SUCCESS` | JSON true/false: tratamiento de completion por límite de tokens en SDK |
| `DSH_TELEMETRY_DISABLED` / `DSH_TELEMETRY_MODE=DISABLED` | Telemetría OTLF (`dsh/lib/bin.js`, `dsh-http-proxy`) |
| `DSH_LAUNCH_ENVIRONMENT_KEY` | Key del snapshot de entorno de launch (`dsh/lib`, `dsh-app-boot`) |
| `DEEPSEEK_API_KEY` | Credencial del adapter DeepSeek (`apiKeyEnv` en sdk-minimal) |
| `http_proxy`/`https_proxy`/`no_proxy`/`all_proxy` (+ mayúsculas) | Política de proxy outbound (`dsh-http-proxy`) |

(Otras `DSH_*` internas observadas en lib: `DSH_SESSION_ID`, `DSH_SHELL`, `DSH_SUBPROCESS_RUNNER`, `DSH_PTY_SESSION_ID`, `DSH_WEB_FETCH_PROVIDER`, `DSH_WEB_SEARCH_PROVIDER`, `DSH_SNAPSHOT`, y variables de protocolo de terminal persistente.)

### Guías de extensión referenciadas
- `docs/user/guide/github-review.md` — webhooks de review GitHub (regla, puerto dedicado, secret, routing de Workspace).
- `docs/user/guide/mcp-memory.md` — tres overlays de servidores MCP de memoria.
- `docs/user/guide/schedule.md` — mounting de Schedule con time-context.
- `docs/user/guide/network-proxy.md` — qué exportar para el proxy.
- `docs/cookbook/extension-cookbook.md` — dsh-acp como ejemplo worked para autores de extensiones.
- `docs/config-catalog.md` — catálogo generado exhaustivo de campos de config por paquete.
- `docs/subsystems/{tools,skills,schedule}.md` — contratos de subsistemas.
- Notas de diseño en `.agents/notes/**` (mcp-client, hook-bridges, ACP, profile-plugin-bundles…).

---

## 10. Inventario publicado (contexto)

El directorio `@deepseek-ai/` contiene ~190 paquetes. Los paquetes estudiados se agrupan así:
- **Puentes/compat**: `dsh-mcp-client`, `dsh-hooks-claude-code`, `dsh-hooks-codex`, `dsh-hook-protocol`.
- **Producto opt-in**: `dsh-webhook`, `dsh-webhook-github`, `dsh-schedule`, `dsh-skill`, `dsh-skill-filesystem`, `dsh-http-proxy`.
- **Superficies/perfiles**: `dsh-base`, `dsh-web-app`, `dsh-headless`, `dsh-acp`/`dsh-acp-app`, `dsh-sdk-*`.
- **Core**: `dsh-agent`, `dsh-session`, `dsh-tools`, `dsh-llm*`, `cordis*`.

Los overlays de ejemplo (`config/examples/` del repo: GitHub review, schedule, memory MCP, runtime Cordis tools) **no se publican en el paquete npm** (`dsh/package.json` `files: ["lib/*.js"]`); las instrucciones de setup viven en las guías de usuario enlazadas.
