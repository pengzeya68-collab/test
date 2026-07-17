# TestMaster Desktop UI Automation Implementation Specification

Status: implementation contract  
Target: Windows 10/11, Chromium, web UI automation  
Existing stack: Vue 3 + Vite + Element Plus, FastAPI, PostgreSQL, Redis/Celery  
Desktop stack: Electron + Node.js + Playwright

This document is normative. An implementation is not complete because a page
renders or a demo can click a button. It is complete only when the acceptance
criteria and required automated tests in this document pass.

## 1. Product Goal

Build an enterprise-usable web UI automation capability without rewriting the
existing TestMaster web platform.

The finished product must let a tester:

1. Create and organize UI cases in the existing platform.
2. Record browser operations through a desktop application.
3. Edit recorded operations as maintainable structured steps.
4. Debug a case locally with pause, resume, stop, breakpoints, and single-step.
5. Run cases, suites, and data-driven iterations reliably through Playwright.
6. Inspect screenshots, video, trace, console, network, and step-level errors.
7. Run the same case locally, on a dedicated agent, or from CI.
8. Store cases, versions, execution summaries, permissions, and audit data on
   the server while keeping transient browser execution local to the agent.

## 2. Non-Goals For Version 1

Do not implement these in the first production release:

- Windows native application automation.
- Android or iOS automation.
- Coordinate-based operation as a normal locator strategy.
- Image recognition as a normal locator strategy.
- AI locator self-healing that silently changes saved cases.
- Firefox or WebKit execution before Chromium acceptance passes.
- A second independent account, RBAC, report, environment, or scheduler system.
- A Python Selenium execution engine.
- Arbitrary JavaScript execution without explicit permission and audit logging.

The UI and data model may expose extension points for these features, but they
must not add untested execution paths to version 1.

## 3. Architecture

Use a hybrid architecture:

```text
TestMaster Server
  Vue management UI
  FastAPI APIs
  PostgreSQL: cases, versions, runs, metadata
  Redis/Celery: server scheduling and agent dispatch
          |
          | HTTPS + authenticated WebSocket
          v
TestMaster Desktop / Headless Agent
  Electron main process
  Existing Vue renderer build
  Typed preload IPC bridge
  Local Node execution worker
  Playwright + pinned Chromium
  Local artifact spool and upload queue
```

### 3.1 Ownership boundaries

Server owns:

- Users, projects, RBAC, environments, secrets metadata, UI cases, suites,
  versions, schedules, run records, audit records, and artifact indexes.
- Agent registration, assignment, heartbeat, revocation, and run cancellation.
- Final authoritative run status.

Desktop agent owns:

- Browser installation verification and launch.
- Recording, locator inspection, local debugging, and Playwright execution.
- Temporary auth state, screenshots, videos, traces, and local run logs.
- Buffered event and artifact upload during temporary network interruption.

Renderer must never own:

- Direct Node.js filesystem access.
- Playwright browser objects.
- Raw database credentials or long-lived agent secrets.
- Unrestricted Electron IPC.

### 3.2 Required new directories

```text
desktop/
  package.json
  electron-builder.yml
  src/main/
  src/preload/
  src/shared/contracts/
  src/worker/
  tests/
frontend/src/views/ui-automation/
frontend/src/components/ui-automation/
frontend/src/api/ui-automation.js
fastapi_backend/models/ui_automation.py
fastapi_backend/schemas/ui_automation.py
fastapi_backend/routers/ui_automation.py
fastapi_backend/services/ui_automation/
fastapi_backend/tests/test_ui_automation_*.py
e2e/ui-automation/
```

Do not put the execution engine in a Vue component or a FastAPI route.

## 4. Technology Decisions

### 4.1 Electron

- Use a currently supported stable Electron version, pinned exactly.
- `contextIsolation: true`.
- `nodeIntegration: false`.
- `sandbox: true` where compatible with the preload bridge.
- Disable navigation to untrusted origins in the application window.
- Deny unexpected permission requests.
- Use Electron Builder for signed NSIS packaging.
- Support silent unattended installation for enterprise deployment.

### 4.2 Playwright

- Use `playwright`, not Selenium and not custom CDP wrappers.
- Pin Playwright and browser revisions in the lockfile.
- Chromium is the only required version 1 browser.
- Use Locator APIs and Playwright auto-waiting.
- Never add unconditional sleeps as the default synchronization strategy.
- Enable trace, screenshot, and video according to the run profile.

### 4.3 Shared contracts

Use TypeScript for Electron main, preload, worker, and IPC contracts.

Every IPC call and worker message must have:

- A named request and response type.
- Runtime validation with Zod or an equivalent schema validator.
- A correlation ID.
- A defined error code.
- A timeout and cancellation behavior.

## 5. Security Model

### 5.1 Authentication

- Desktop login uses the existing server authentication flow.
- Store refresh credentials in Windows Credential Manager, never localStorage.
- Agent registration returns a revocable agent credential scoped to that agent.
- WebSocket reconnect must refresh expired access tokens safely.
- Logout deletes local credentials, browser storage state, and sensitive spool
  data after pending uploads are resolved or explicitly discarded.

### 5.2 Secrets

- Environment secrets must be encrypted server-side using the existing
  encryption mechanism.
- API responses return masked secret values by default.
- The agent receives resolved secrets only for an authorized assigned run.
- Secret values must be redacted from logs, screenshots metadata, network
  payload previews, reports, and error messages.
- The renderer receives secret references, not plaintext values.

### 5.3 Script execution

- `evaluate` or custom script steps are disabled by default per project.
- Enabling them requires a dedicated permission.
- Record script creation, modification, and execution in the audit log.
- Display a persistent warning on cases containing scripts.
- Do not claim JavaScript executed in a browser context is a secure sandbox.

### 5.4 SSRF and navigation policy

- Reuse the platform's environment allowlist policy.
- Provide project-level allowed host patterns.
- Block `file:`, `javascript:`, browser internal pages, and unexpected local
  network targets unless an administrator explicitly allows them.
- Redirects must be checked against the same navigation policy.

## 6. Domain Model

Create Alembic migrations. Do not create columns at runtime.

### 6.1 `ui_cases`

- `id`, `project_id`, `group_id`, `name`, `description`
- `user_id`, `owner_id`, `status`, `priority`, `tags`
- `base_url`, `default_timeout_ms`, `navigation_timeout_ms`
- `viewport`, `locale`, `timezone_id`, `color_scheme`
- `storage_state_ref`, `is_active`
- `current_version_id`, `created_at`, `updated_at`

Rules:

- Names are required and limited to 200 characters.
- All reads and writes are scoped by user/project permissions.
- Delete is soft-delete unless no execution/version references exist.

### 6.2 `ui_case_versions`

- `id`, `case_id`, `version_number`, `snapshot_json`
- `change_summary`, `created_by`, `created_at`, `is_current`

`snapshot_json` contains an immutable complete case execution definition.
Runs always reference a version, never an editable live case.

### 6.3 `ui_steps`

The editable table may be normalized, but the execution snapshot must use:

```json
{
  "id": "stable-uuid",
  "order": 10,
  "name": "Submit login",
  "type": "click",
  "enabled": true,
  "breakpoint": false,
  "locator": {
    "strategy": "role",
    "value": "button",
    "options": { "name": "Login", "exact": true },
    "fallbacks": []
  },
  "input": null,
  "timeout_ms": null,
  "retry": { "count": 0, "delay_ms": 0 },
  "continue_on_failure": false,
  "screenshot": "on-failure",
  "condition": null,
  "children": []
}
```

Step IDs must remain stable when reordered.

### 6.4 `ui_suites` and `ui_suite_items`

- Suite metadata belongs to a project.
- Items reference case ID and optional pinned version ID.
- Items support order, enabled state, data source, and per-case overrides.
- Define whether a suite stops on first case failure.

### 6.5 `ui_runs`

- `id`, `run_key` UUID, `project_id`, `case_id`, `case_version_id`, `suite_id`
- `agent_id`, `trigger_type`, `triggered_by`
- `status`, `queued_at`, `started_at`, `finished_at`
- `browser`, `browser_version`, `desktop_version`, `engine_version`
- `environment_id`, `dataset_iteration`, `retry_of_run_id`
- `total_steps`, `passed_steps`, `failed_steps`, `skipped_steps`
- `error_code`, `error_summary`, `artifact_manifest`

Status transitions are strictly:

```text
queued -> assigned -> starting -> running -> passed|failed|cancelled|error
queued|assigned -> cancelled
assigned|starting -> orphaned -> queued|error
```

Transitions must use conditional database updates to prevent stale agents from
overwriting a terminal status.

### 6.6 `ui_step_results`

- `run_id`, `step_id`, `iteration`, `attempt`
- `status`, `started_at`, `finished_at`, `duration_ms`
- `resolved_locator`, `input_preview`, `error_code`, `error_message`
- `screenshot_artifact_id`, `trace_event_ref`

### 6.7 `desktop_agents`

- `id`, `agent_key`, `name`, `owner_id`, `team_id`
- `hostname`, `os_version`, `desktop_version`
- `capabilities`, `status`, `last_heartbeat_at`
- `max_parallel`, `current_runs`, `revoked_at`

Never trust hostname or capability fields for authorization.

### 6.8 Artifacts

Store artifact metadata in PostgreSQL and binary content in configurable object
storage or local server storage. Artifact paths must not be user-controlled.

Required artifact types:

- Screenshot
- Video
- Playwright trace ZIP
- Console log JSONL
- Network summary JSONL
- Downloaded file, when explicitly retained
- HTML summary report

Define retention policy per project and a cleanup job with audit records.

## 7. Supported Step Types

Version 1 must support these types with documented input schemas:

### Navigation and browser

- `goto`
- `reload`
- `go_back`
- `switch_page`
- `close_page`
- `set_viewport`
- `use_storage_state`

### Element operations

- `click`
- `double_click`
- `fill`
- `type` for key-by-key input only when specifically needed
- `clear`
- `press`
- `check`
- `uncheck`
- `select_option`
- `hover`
- `focus`
- `scroll_into_view`
- `drag_and_drop`
- `upload_file`
- `download`

### Context

- `within_frame`
- `exit_frame`
- `wait_for_popup`
- `accept_dialog`
- `dismiss_dialog`

### Waits

- `wait_for_element`
- `wait_for_url`
- `wait_for_response`
- `wait_for_load_state`
- `wait_for_timeout`, visibly marked as discouraged

### Assertions

- Visible, hidden, enabled, disabled, editable, checked
- Text equals, contains, matches regular expression
- Value, attribute, CSS property
- Element count
- URL and title
- Screenshot comparison, optional and feature-flagged until stable
- HTTP response status and selected JSON field

### Variables and control flow

- Set variable
- Extract text, value, attribute, URL, or JSON response value
- If/else
- For-each over a bounded list
- Reusable step group
- Call another UI case with recursion detection

Control flow must enforce maximum nesting, iteration, and referenced-case depth.

## 8. Locator Model

Supported locator strategies, in preferred order:

1. `test_id`
2. `role`
3. `label`
4. `placeholder`
5. `text`
6. `css`
7. `xpath`

Each locator stores strategy, value, structured options, frame path, and zero or
more fallbacks. Coordinates are not a saved locator strategy in version 1.

### 8.1 Recording locator generation

Recorder generation order:

1. Unique configured test ID.
2. Role plus accessible name.
3. Associated label.
4. Stable placeholder or visible text.
5. Stable attributes and short CSS.
6. Relative XPath only if no better strategy works.

Reject generated selectors containing volatile IDs, long `nth-child` chains,
absolute `/html/body` XPath, or framework-generated class hashes unless the
user explicitly confirms them.

### 8.2 Locator inspection

The desktop inspector must:

- Highlight all matches and show match count.
- Show why the recommended locator was chosen.
- Let users switch strategy and test it live.
- Detect strict-mode violations before saving.
- Capture accessible role/name and useful stable attributes.
- Never silently replace a saved locator during execution.

## 9. Execution Semantics

### 9.1 Isolation

- Each case iteration gets a new BrowserContext by default.
- A suite may explicitly share storage state, not a mutable BrowserContext.
- Downloads and temporary files use a run-specific directory.
- Cleanup runs in `finally`, even after cancellation.

### 9.2 Timeouts

- Action default: 10 seconds.
- Assertion default: 5 seconds.
- Navigation default: 30 seconds.
- Case maximum duration is configurable and enforced.
- Step timeout overrides are bounded by project policy.

### 9.3 Retry

- Locator actions default to zero explicit retries because Playwright already
  auto-waits.
- Case retry is configured at suite/run level.
- Every retry is a separate attempt with artifacts and status.
- A passed retry does not erase the original failure.

### 9.4 Cancellation

- Stop requests are idempotent.
- The worker closes page/context/browser and marks unfinished steps cancelled.
- Force-kill is permitted after a bounded graceful shutdown period.
- The server ignores late non-terminal events after a terminal transition.

### 9.5 Offline behavior

- Local debug may run while the server connection is temporarily unavailable
  if the version snapshot is already downloaded.
- Events are written to an append-only local spool before transmission.
- Reconnect uploads events idempotently using run key and sequence number.
- A user must be warned before deleting pending artifacts.

## 10. Desktop User Experience

Do not copy the dated dialog-and-table appearance in the reference images.
Use the existing Element Plus visual language and a dense work-oriented layout.

### 10.1 Main layout

```text
Top: project, environment, agent state, record/run/debug controls
Left: case/group tree with search and tags
Center: ordered step editor
Right: selected step properties, locator inspector, variables
Bottom: run log, console, network, artifacts, problems tabs
```

Panels must be resizable and persist their dimensions locally.

### 10.2 Case editor

- Virtualized step list for large cases.
- Drag reorder plus keyboard-accessible move commands.
- Add, duplicate, disable, delete, group, breakpoint.
- Undo and redo.
- Unsaved-change indicator and conflict handling.
- Validation problems shown inline and in a Problems tab.
- Save creates a version only when execution-affecting content changes.

### 10.3 Run controls

- Record
- Run
- Debug
- Run selected step
- Run from selected step, only after prerequisites are confirmed
- Pause/resume
- Stop

Do not pretend arbitrary mid-case execution is safe. The UI must warn when the
selected step depends on missing navigation, authentication, frame, or variable
state.

### 10.4 Result view

- Timeline of steps and attempts.
- Clear classification: assertion failure, locator failure, timeout, browser
  crash, environment error, cancelled, infrastructure error.
- Screenshot before/after failure where available.
- Embedded or launched Playwright Trace Viewer.
- Console and network events correlated by step time.
- Direct links to case version, environment, agent, and retry run.

## 11. Recorder

Implement recording as a separate controlled browser session.

Required behavior:

- Record navigation, click, fill, select, check, upload, popup, and dialog.
- Coalesce repeated keystrokes into a single fill step.
- Do not record passwords or fields marked sensitive; save a secret reference.
- Allow pause/resume and removal of accidental actions before import.
- Generate a draft; recording never directly overwrites a case version.
- Present locator quality and warnings before accepting steps.
- Capture assertions through an explicit "add assertion" mode.

Do not build recording by globally capturing Windows mouse coordinates.

## 12. Server APIs

Follow existing FastAPI router, schema, RBAC, audit, pagination, and error
response conventions.

Required API groups:

```text
/api/ui-automation/cases
/api/ui-automation/cases/{id}/versions
/api/ui-automation/suites
/api/ui-automation/runs
/api/ui-automation/runs/{id}/events
/api/ui-automation/runs/{id}/artifacts
/api/ui-automation/agents
/api/ui-automation/schedules
```

Required behaviors:

- Optimistic locking using `updated_at` or revision number.
- Idempotency key for run creation and event upload.
- Tenant ownership check from the database on every object operation.
- Pagination and bounded filters for list APIs.
- Artifact upload uses size/type limits and server-generated paths.
- Run event batches require monotonic sequence numbers.
- API errors use stable machine-readable codes.

### 12.1 WebSocket

Use WebSocket for agent commands and live events, with REST fallback for state
reconciliation.

Messages include:

- `agent.hello`, `agent.heartbeat`, `agent.capabilities`
- `run.assign`, `run.accept`, `run.reject`
- `run.event_batch`, `run.cancel`, `run.finished`
- `record.event`, `debug.command`, `debug.state`

Delivery is at-least-once; handlers must be idempotent.

## 13. Agent Scheduling

- A run is assigned only to an online, authorized, compatible agent.
- Use database/Redis locking so one run cannot be assigned twice concurrently.
- Agent acceptance has a deadline.
- Missed heartbeats mark active assignments orphaned after a grace period.
- Orphan retry policy is explicit and bounded.
- Scheduled UI runs target an agent pool, not an arbitrary user's workstation.
- Desktop interactive sessions default to `max_parallel = 1`.
- Headless agents may configure bounded parallelism based on resources.

## 14. Reports And Diagnostics

An enterprise report must answer:

- What was executed?
- Which immutable version and data iteration were used?
- Where and with which browser/agent version did it run?
- What failed first?
- Is it a product assertion, locator, data, environment, or infrastructure issue?
- What evidence is available?

Minimum report contents:

- Summary counts and duration.
- Case/suite/version/environment metadata.
- Step timeline with attempts.
- Sanitized error and stack.
- Screenshot, video, trace links.
- Console errors and failed network requests.
- Retry relationship and historical trend.

Reuse existing report infrastructure where practical. Do not create a report
that exists only as a local HTML file on one tester's computer.

## 15. Packaging And Updates

- Produce a signed Windows installer and portable build for internal testing.
- Never require administrator privileges for normal execution.
- Install Playwright Chromium deterministically.
- Verify required browser binaries on startup and provide repair action.
- Auto-update uses a signed update manifest and supports staged rollout.
- Preserve settings and pending artifact spool across upgrades.
- Support rollback to the previous desktop version.
- Expose desktop, Electron, Node, Playwright, and browser versions in About and
  every run record.

## 16. Observability

- Structured JSON logs with correlation IDs.
- Separate application, worker, and run logs.
- Rotate local logs and redact secrets.
- Agent health includes queue depth, disk space, browser readiness, and last
  server round-trip.
- Server metrics include queued runs, assignment latency, orphaned runs,
  execution duration, failure category, artifact upload failure, and agent count.
- Provide a diagnostic bundle export with user confirmation and redaction.

## 17. Implementation Phases And Gates

Do not implement all features in one uncontrolled branch. Each phase has a gate.

### Phase 0: Architecture baseline

Deliver:

- Architecture decision records.
- TypeScript workspace and Electron secure window.
- Typed IPC proof.
- Playwright launch proof with pinned Chromium.
- Server feature flag `UI_AUTOMATION_ENABLED`.

Gate:

- Security settings test passes.
- Desktop starts, logs in, launches/closes Chromium without orphan processes.
- Existing web build and backend tests are unchanged or passing.

### Phase 1: Local execution vertical slice

Deliver:

- Case model, version model, CRUD APIs.
- Step editor for goto, click, fill, visible/text assertion.
- Local run worker and step event stream.
- Screenshot and trace on failure.
- Basic result page.

Gate:

- A fixed demo application runs 100 consecutive times with at least 99% pass
  rate and no browser processes left behind.
- Restarting the desktop app does not corrupt saved cases.
- Unauthorized users cannot access another user's cases or runs.

### Phase 2: Recorder and debugger

Deliver:

- Recorder draft workflow.
- Locator inspector and quality warnings.
- Breakpoint, pause, resume, stop, single-step.
- Console/network tabs.

Gate:

- Recorded login/search/upload/popup cases can be edited and rerun.
- Passwords never appear in saved drafts or logs.
- Cancellation completes within the defined shutdown limit.

### Phase 3: Enterprise execution

Deliver:

- Agent registration/heartbeat/assignment.
- Suites, datasets, environment resolution, secret references.
- Server schedules and CI/headless command.
- Artifact upload, retention, and historical reports.

Gate:

- Duplicate assignment and offline recovery tests pass.
- The same immutable case version produces equivalent behavior locally and on a
  headless agent.
- Network interruption and reconnect do not duplicate step results.

### Phase 4: Packaging and hardening

Deliver:

- Signed installer, updater, rollback, diagnostics.
- Performance, security, soak, and compatibility results.
- Operator and tester documentation.

Gate:

- 8-hour repeated execution has no material memory/process leak.
- Upgrade and rollback preserve cases/settings/pending artifacts.
- Clean Windows 10 and Windows 11 virtual machines pass install-to-run tests.

## 18. Required Test Strategy

### 18.1 Unit tests

- Step schema validation and migration.
- Locator generation and rejection rules.
- Variable resolution and secret redaction.
- State machine transitions.
- Retry, timeout, cancellation, and control-flow limits.
- IPC runtime validation.

### 18.2 Contract tests

- Vue/preload IPC contract.
- Electron/worker protocol.
- Agent/server WebSocket protocol.
- Artifact manifest and upload API.
- Version snapshot backward compatibility.

### 18.3 Integration tests

Build a deterministic local test site containing:

- Delayed elements and API responses.
- iframe and nested iframe.
- Popup/new tab.
- Dialogs.
- Upload and download.
- Shadow DOM.
- Dynamic but semantically stable elements.
- Failed HTTP calls and console errors.
- Authentication and storage-state scenarios.

Every supported step type must have success, failure, timeout, and cancellation
coverage where applicable.

### 18.4 Desktop E2E

Automate critical workflows:

- Install/start/login/logout.
- Create/edit/version a case.
- Record and import a draft.
- Run/debug/stop a case.
- Inspect artifacts.
- Disconnect/reconnect.
- Upgrade/rollback.

### 18.5 Compatibility matrix

Version 1 release matrix:

- Windows 10 current supported build.
- Windows 11 current supported build.
- 100%, 125%, and 150% display scaling.
- Chinese and English Windows locale.
- Standard user without administrator rights.
- Direct network and authenticated corporate proxy.
- Server with valid certificate and documented internal CA setup.

### 18.6 Non-functional targets

- Desktop idle memory target: under 300 MB excluding browser.
- No orphan browser/worker process after normal completion or cancellation.
- 10,000-step result list remains usable through virtualization.
- Live event UI remains responsive under 100 events/second.
- Artifact upload resumes after network interruption.
- Secret redaction test corpus has zero known leaks.

## 19. Definition Of Done

A feature is done only when:

- Code follows existing project conventions.
- Alembic migration and rollback are supplied.
- Permission and tenant-isolation tests exist.
- Unit, contract, integration, and relevant E2E tests pass.
- Failure paths and cancellation are implemented.
- Logs and errors are actionable and sanitized.
- User-facing documentation is updated.
- No unrelated refactor or generated artifact is committed.
- A reviewer can trace each acceptance criterion to code and a test.

The overall feature is not production-ready until all phase 4 gates pass.

## 20. Prohibited Shortcuts

Reject an implementation that does any of the following:

- Merely wraps the current website in Electron and calls it UI automation.
- Runs Playwright directly from the Vue renderer.
- Enables `nodeIntegration` to simplify implementation.
- Stores tokens or secrets in localStorage or plaintext files.
- Uses absolute XPath or coordinates as the recorder default.
- Implements waits primarily with fixed sleep.
- Saves recorded steps directly without a draft/review stage.
- Mutates a case while an execution is using it instead of version snapshots.
- Reports only pass/fail without traceable step evidence.
- Treats retry success as if the first attempt never failed.
- Shares a mutable BrowserContext across unrelated cases.
- Trusts agent-provided user/project IDs for authorization.
- Adds runtime database migrations instead of Alembic.
- Declares completion without deterministic fixture-site testing.

## 21. Instructions For The Implementing AI

Before coding:

1. Read this entire specification.
2. Inspect existing router registration, authentication, RBAC, audit, database,
   environment, suite, scheduler, task store, report, and frontend layout code.
3. Produce a file-level implementation plan and map every phase gate to tests.
4. Identify existing dirty worktree changes and preserve them.
5. Implement only one phase at a time.

For every phase submission, provide:

- Changed-file list and architectural rationale.
- Database migration details.
- API/IPC contract changes.
- Security considerations.
- Exact automated test commands and results.
- Screenshots of the desktop UI at 100%, 125%, and 150% scaling.
- Known limitations and the next phase boundary.

Do not claim the complete product is finished after a prototype or phase 1.

## 22. Review Checklist For Codex

The later code review will prioritize, in this order:

1. Tenant isolation, secret handling, Electron boundary security.
2. Run state correctness, idempotency, cancellation, offline recovery.
3. Browser/context/process cleanup and execution determinism.
4. Locator quality and avoidance of flaky synchronization.
5. Immutable versioning and reproducible reports.
6. Agent scheduling and duplicate execution prevention.
7. Test depth, compatibility evidence, and upgrade safety.
8. Usability for repeated daily work, not only visual appearance.

Any P0/P1 finding in these areas blocks acceptance regardless of demo quality.
