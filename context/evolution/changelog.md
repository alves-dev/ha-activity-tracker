# Changelog

## 2026-09-10

- Replaced the Activity Rules native-flow host with a complete draft editor.
  Activities can now be created and edited on one themed sidebar screen with
  model, recursive AND/OR start/stop rules, state-duration, report-silence,
  templates, behavior, retention, periods, metrics, and midnight policy.
- The browser only holds drafts. An admin-only integration WebSocket contract
  validates, previews template and condition results, produces the review diff,
  and applies changes; it never lets browser code update a ConfigEntry.
- A rule or midnight-policy change now shows the server-computed history impact
  and cannot be applied until the administrator explicitly confirms clearing
  retained history.
- Fixed the review action method collision, made custom condition field order
  more natural, and exposed explicit matched/not-matched status for each live
  condition.
- Added numeric state/attribute conditions with exact decimal threshold
  comparisons and the same pending-duration behavior as state conditions.
- Activity editing is now exposed only in the Activity Rules sidebar, and its
  icon uses `mdi:clock-outline` to match the integration artwork.

## 2026-09-10 — Painel lateral Activity Rules

- Adicionado um painel lateral somente para administradores com todos os
  monitores, árvores de início/término, estado atual, resultado de templates e
  prazos pendentes.
- O painel acompanha o tema claro, escuro ou personalizado do Home Assistant e
  apresenta rótulos em português quando a interface está em pt-BR.
- A criação e edição são hospedadas no fluxo nativo da integração pelo painel,
  sem duplicar validação ou confirmação de histórico.

## 2026-09-10 — Regras de atividade por template

- Adicionado o template **Regra por template**, com expressões booleanas
  independentes para iniciar e terminar uma atividade.
- As expressões usam o mecanismo nativo de templates do Home Assistant; assim,
  alterações em entidades e atributos consultados reavaliam a atividade sem
  exigir entidades auxiliares ou polling.
- Documentado o plano do painel lateral **Activity Rules**, com árvore visual
  AND/OR, inspetor de componentes e estados ao vivo.

## 2026-09-10 — Inspeção e controle de regras durante a edição

- A edição de uma regra personalizada agora começa pelas condições de início e
  término já salvas, permitindo adicioná-las ou removê-las sem reconstruir a
  atividade às cegas.
- Cada tela de condição mostra uma fotografia do estado atual: resultado da
  expressão, estado observado e prazo restante para condições temporizadas ou
  de ausência de reportes.
- Foi mantida a edição pelo fluxo nativo do Home Assistant; uma página lateral
  em tempo real foi deliberadamente adiada para uma necessidade futura de
  controle entre vários monitores.

## 2026-09-09 — Refatoração por regras unificadas entregue

- Entregue o motor único de `start_when` e `stop_when`, com condições de estado,
  estado por duração e ausência de reportes, combinadas por AND/OR.
- A criação e edição percorrem template, fonte, condições, comportamento,
  períodos e métricas; a edição de regra ou política de meia-noite confirma a
  limpeza do histórico incompatível.
- Removidos tipos legados, Recorder, migrações, tempo desconhecido, políticas
  globais de indisponibilidade e documentação associada.
- Entregues dias históricos fechados, médias circulares de horário, atribuição
  configurável na meia-noite e o contrato estatístico diário `sum`.

## 2026-09-09 — Planejamento da refatoração por regras unificadas

- Aprovado o plano para substituir tipos de monitor por regras personalizadas de
  início e término combináveis com AND/OR, com o único template inicial de
  presença em zona.
- Confirmado que configurações, entidades e armazenamento da versão anterior
  serão removidos antes da instalação; não haverá migração de compatibilidade.
- A reconstrução e reimportação pelo Recorder foram removidas do escopo, pois
  regras compostas e temporizadas não podem ser reconstituídas com fidelidade.
- Definido que `Last 1` representa ontem, e não o dia em andamento.

## 2026-09-08 — Monitor de celular em uso

- Adicionado o tipo de monitor **Celular em uso**, configurado pela seleção de
  um único dispositivo Android do Home Assistant Companion App.
- O monitor encontra e valida automaticamente as entidades `Interactive` e
  `Last update trigger`, encerrando ou tratando a sessão como indisponível quando
  o celular deixa de se comunicar pelo limite configurado (30 minutos por
  padrão).
- Relatórios de heartbeat sem mudança de estado agora são reconhecidos; um
  heartbeat isolado nunca reabre uma sessão de tela antiga.
- A validação agora usa os IDs de entidade visíveis do dispositivo e informa no
  formulário os IDs esperados quando as entidades obrigatórias não forem
  encontradas.
- Corrigida a classificação da entidade `Interactive`: o estado `on` agora inicia
  corretamente uma sessão, sem exigir uma lista genérica de estados ativos.

## 2026-08-31 — Correção dos assets de marca

- Corrigido o conjunto de ícones e logos da integração com variantes claras e
  escuras distintas, transparência e resoluções normais e de alta densidade
  compatíveis com o padrão de integrações Home Assistant.

## 2026-08-31 — Seleção de sensores por período

- Sensores de relatório agora são selecionados individualmente para cada período
  escolhido; por exemplo, a média de duração de sessão pode existir somente para
  os últimos 30 dias, sem um sensor equivalente para hoje.
- Monitores existentes são migrados de forma compatível, mantendo os mesmos
  pares de sensores até que o usuário altere a configuração.

## 2026-08-28 — SonarQube follow-up cleanup

- Simplified diagnostics import-result construction and replaced mutation-safe
  list snapshots with tuple snapshots in runtime cleanup paths.

## 2026-08-28 — SonarQube maintainability remediation

- Split Recorder querying from interval reconstruction and extracted runtime
  session-transition and daily-summary helpers, preserving the existing
  accounting contracts while reducing cognitive complexity.

## 2026-08-28 — Local Home Assistant helper standardization

- Aligned the local Home Assistant start and stop helpers with the shared PID
  file convention and documented the integration deployment helper for agents.

## 2026-08-28 — Documentação de monitores e sensores

- Adicionadas ao README as tabelas dos cinco tipos de monitor e dos quinze
  sensores de relatório selecionáveis, incluindo como os sensores são criados.
- Adicionados casos de uso separados para cada tipo de monitor em `docs/` e
  vinculados a partir da tabela do README.
- Cada caso de uso agora apresenta o conteúdo em PT-BR e inglês no mesmo
  arquivo, identificado pelos rótulos `[pt-BR]` e `[en]`.
- As tabelas de tipos de monitor e sensores selecionáveis no README também têm
  versões em PT-BR e inglês identificadas pelos mesmos rótulos.

## 2026-08-28 — Local integration deployment

- Added `dev/copy-to-core.sh` to stop the local Home Assistant instance, deploy
  Activity Tracker to its configuration directory, and start the instance again.

## 2026-08-28 — Per-monitor duration display

- Added a presentation-only duration unit for each monitor: hours, minutes, or
  seconds. New monitors default to hours; existing monitors preserve seconds
  until edited.

## 2026-08-28 — Administrative UX and diagnostics

- Added explicit confirmation before a monitor edit clears retained history or
  requests a Recorder reimport; presentation-only edits now save directly.
- Added redacted monitor diagnostics and actionable availability attributes
  without exposing activity, location, or application history.

## 2026-08-27 — Phase 5 proposal

- Proposed the administrative-history confirmation and redacted-diagnostics
  contract for approval before implementation.

## 2026-08-27 — Recorder import reliability

- Moved optional Recorder reconstruction to a post-startup background task.
- Rebuilt only Recorder-backed dates while preserving retained summaries outside
  that range, with idempotent replacement and partial boundary-day quality.
- Recorded a compact import outcome with range, rebuilt/preserved days, processed
  sessions, and safe warnings; historical foreground-app attributes now follow
  the configured attribute selection.
- Fixed the SonarQube workflow to use the project's canonical analysis endpoint.

## [Fix] - Zone Monitor State Matching

- Corrected zone monitors to compare person and device-tracker states with the
  Home Assistant zone value (`home` or the zone name), rather than `zone.*` IDs.

## [Developer Experience] - Local Home Assistant Control

- Added `dev/start-ha.sh` and `dev/stop-ha.sh` to start and gracefully stop the
  isolated local Home Assistant test instance, with its PID and logs kept under
  `/tmp`.
- Made both scripts POSIX `sh` compatible so they can be invoked with `sh` or
  directly.
- Documented the local instance lifecycle and exploratory-test access constraints
  in `AGENTS.md`.

## [Current State] - Context Mesh Added

### Existing Features (documented)

- Flexible activity monitoring - independent monitors for state, zone, area-presence, and general activity.
- Guided monitor management - UI setup and editing with selected periods and measurements.
- Activity reporting - duration, counts, session details, statistics, and calendar-based reports.
- Durable activity history - retained daily summaries with optional historical reconstruction.
- Foreground application insights - current-app and application-switch activity tracking.

### Tech Stack (documented)

- Python 3.14 and Home Assistant 2026.8.
- `uv`, pytest, pytest-asyncio, pytest-cov, and Ruff.
- Home Assistant config entries, entity platforms, event helpers, storage, and Recorder history APIs.

### Patterns Identified

- Activity state classification.
- Calendar-day session aggregation.
- Multi-step configuration flow.
- Selected metric entity factory.

---

*Context Mesh added: 2026-08-27*
*This changelog documents the state when Context Mesh was added.*
*Future changes will be tracked below.*

## [Documentation] - Legacy Specification Consolidated

- Moved the product and engineering scope of the retired implementation specification into Context Mesh through [legacy specification traceability](legacy-specification-traceability.md).
- Explicitly identified requirements that remain partial or planned so existing-code documentation does not overstate implementation status.

## [Planning] - Remaining MVP Gaps

- Added a proposed, phased implementation plan for the incomplete MVP requirements. No implementation is authorized by this entry.
- Drafted proposed ADRs for interruption handling, data-quality completeness,
  migration/import safety, and local calendar boundaries. They are awaiting
  approval and do not authorize implementation.

## [Planning] - Data-Correctness Contracts Approved

- Accepted ADRs 006–009 and added the detailed phase 1–3 execution plan.
- No product code has been changed; a separate execution request is required
  before implementation starts.

## [Implementation] - Data Correctness

- Added an interruption-aware session checkpoint that excludes observed pauses
  and unavailable time from activity totals while retaining logical sessions.
- Added unknown-time accounting, restart-safe checkpoint closure, and exact
  interruption deadlines.
- Migrated durable payloads to schema v2 with atomic writes, safe migration
  failure handling, and per-monitor import/clear serialization.
- Added structured rolling-history availability attributes and local-week support.
- Added focused regression coverage for merge gaps, unavailable time, migration,
  and report availability.

## [Development Tooling] - Local Home Assistant Startup

- Updated the local Home Assistant start script to isolate its runtime from the
  integration virtual environment and wait for the HTTP service to become ready.
