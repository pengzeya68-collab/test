import * as os from 'os';
import { createHash } from 'crypto';
import { readFile, stat } from 'fs/promises';
import * as path from 'path';
import {
  AgentCredentialStore,
  AgentCredentials,
  AgentOutboxArtifact,
  AgentOutboxRecord,
  AgentOutboxStore,
  FileAgentOutboxStore,
  SecureAgentCredentialStore,
} from './agent-state-store';
import {
  CaseExecutionEngine,
  CaseSnapshot,
  EnvironmentConfig,
  RunOptions,
  RunResult,
  StepEvent,
} from '../worker/execution-engine';
import { normalizeAgentServerUrl } from '../shared/safe-url';
import { isBrowserEngineAvailable } from '../worker/browser-runtime';

type AgentLifecycleState = 'unregistered' | 'disabled' | 'starting' | 'online' | 'running' | 'offline' | 'error' | 'stopping';

export interface DesktopAgentStatus {
  state: AgentLifecycleState;
  registered: boolean;
  enabled: boolean;
  agentId: number | null;
  agentKey: string | null;
  name: string | null;
  serverUrl: string | null;
  authStateId: string | null;
  headless: boolean;
  maxParallel: number;
  browserEngine: 'chromium' | 'firefox' | 'webkit';
  activeRunId: number | null;
  activeRunIds: number[];
  lastHeartbeatAt: string | null;
  lastClaimAt: string | null;
  lastError: string | null;
  retryInMs: number | null;
}

export interface AgentRegistrationInput {
  serverUrl: string;
  accessToken: string;
  name: string;
  authStateId?: string | null;
  headless?: boolean;
  maxParallel?: number;
  browserEngine?: 'chromium' | 'firefox' | 'webkit';
  projectId?: number | null;
}

interface AgentRun {
  id: number;
  status: string;
  environment_id?: number | null;
  project_id?: number | null;
  user_id?: number | null;
}

interface AgentEnvironment {
  base_url?: string;
  baseUrl?: string;
  variables?: Record<string, string>;
  secret_keys?: string[];
  secretKeys?: string[];
}

interface CasePlan {
  kind: 'case';
  run_id: number;
  snapshot: CaseSnapshot;
  environment?: AgentEnvironment | null;
}

interface SuitePlanEntry {
  snapshot: CaseSnapshot;
  variables?: Record<string, string>;
}

interface SuitePlan {
  kind: 'suite';
  run_id: number;
  environment?: AgentEnvironment | null;
  plan: {
    stop_on_first_failure?: boolean;
    entries: SuitePlanEntry[];
  };
}

interface ClaimResponse {
  run: AgentRun | null;
  plan?: CasePlan | SuitePlan | null;
}

interface ClaimBatchResponse {
  items?: Array<{ run: AgentRun; plan: CasePlan | SuitePlan }>;
  count?: number;
}

interface EventUploadResponse {
  accepted: number;
  ignored: number;
  last_sequence: number;
  status: string;
}

interface AgentHeartbeatResponse {
  cancel_run_ids?: number[];
}

export interface AgentApi {
  register(input: AgentRegistrationInput, metadata: Record<string, unknown>): Promise<Record<string, any>>;
  heartbeat(credentials: AgentCredentials): Promise<AgentHeartbeatResponse | void>;
  claim(credentials: AgentCredentials): Promise<ClaimResponse>;
  claimBatch?(credentials: AgentCredentials, limit: number): Promise<ClaimBatchResponse>;
  appendEvents(credentials: AgentCredentials, runId: number, events: Record<string, unknown>[]): Promise<EventUploadResponse>;
  uploadArtifact?(credentials: AgentCredentials, runId: number, artifact: AgentArtifactUpload): Promise<void>;
}

interface AgentArtifactUpload {
  kind: 'screenshot' | 'trace' | 'video';
  filename: string;
  contentType: string;
  content: Buffer;
}

export interface AgentExecutionEngine {
  execute(
    snapshot: CaseSnapshot,
    environment: EnvironmentConfig | null,
    options: RunOptions,
    onEvent: (event: StepEvent) => void,
  ): Promise<RunResult>;
  cancel(): Promise<void>;
}

interface DesktopAgentDependencies {
  store?: AgentCredentialStore;
  api?: AgentApi;
  createEngine?: () => AgentExecutionEngine;
  loadAuthState?: (id: string) => object;
  onStatus?: (status: DesktopAgentStatus) => void;
  desktopVersion?: string;
  heartbeatIntervalMs?: number;
  claimIntervalMs?: number;
  runHeartbeatIntervalMs?: number;
  artifactRootDir?: string;
  outboxStore?: AgentOutboxStore;
}

const DEFAULT_HEARTBEAT_MS = 15_000;
const DEFAULT_CLAIM_MS = 3_000;
const DEFAULT_RUN_HEARTBEAT_MS = 12_000;
const DELIVERY_FAILURE_LIMIT_MS = 35_000;

export function normalizeServerUrl(value: string): string {
  return normalizeAgentServerUrl(value);
}

function boundedText(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  return message.replace(/(token|password|secret)\s*[:=]\s*\S+/gi, '$1=[REDACTED]').slice(0, 500);
}

async function delay(ms: number, signal?: AbortSignal): Promise<void> {
  if (signal?.aborted) throw new Error('ABORTED');
  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    timer.unref?.();
    signal?.addEventListener('abort', () => {
      clearTimeout(timer);
      reject(new Error('ABORTED'));
    }, { once: true });
  });
}

async function retryAgentRequest<T>(operation: () => Promise<T>, attempts = 3): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (attempt + 1 < attempts) await delay(300 * (attempt + 1));
    }
  }
  throw lastError;
}

async function fetchJson(url: string, init: RequestInit, timeoutMs = 15_000): Promise<any> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    const text = await response.text();
    let data: any = null;
    if (text) {
      try { data = JSON.parse(text); } catch { data = { detail: text.slice(0, 500) }; }
    }
    if (!response.ok) {
      const detail = typeof data?.detail === 'string' ? data.detail : data?.detail?.message;
      const error = new Error(detail || `AGENT_HTTP_${response.status}`) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }
    return data;
  } finally {
    clearTimeout(timer);
  }
}

async function uploadAgentChunk(url: string, init: RequestInit, timeoutMs = 60_000): Promise<void> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    if (!response.ok) {
      const error = new Error(`AGENT_ARTIFACT_UPLOAD_${response.status}`) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }
  } catch (error) {
    if (controller.signal.aborted) throw new Error('AGENT_ARTIFACT_UPLOAD_TIMEOUT');
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export class HttpAgentApi implements AgentApi {
  async register(input: AgentRegistrationInput, metadata: Record<string, unknown>): Promise<Record<string, any>> {
    const serverUrl = normalizeServerUrl(input.serverUrl);
    const maxParallel = Math.max(1, Math.min(16, Number(input.maxParallel || 1)));
    const browserEngine = input.browserEngine || 'chromium';
    const engineAvailable = isBrowserEngineAvailable(browserEngine);
    return fetchJson(`${serverUrl}/api/ui-automation/agents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${input.accessToken}`,
        ...(Number.isInteger(input.projectId) && Number(input.projectId) > 0
          ? { 'X-Project-Id': String(input.projectId) }
          : {}),
      },
      body: JSON.stringify({
        name: input.name,
        max_parallel: maxParallel,
        ...metadata,
        capabilities: {
          chromium: browserEngine === 'chromium' ? engineAvailable : isBrowserEngineAvailable('chromium'),
          firefox: browserEngine === 'firefox' && engineAvailable,
          webkit: browserEngine === 'webkit' && engineAvailable,
          unattended: true,
          case: true,
          suite: true,
          parallel: maxParallel > 1,
          intercept: true,
          healing: true,
          ...(metadata.capabilities as object || {}),
        },
      }),
    });
  }

  async heartbeat(credentials: AgentCredentials): Promise<AgentHeartbeatResponse> {
    const engine = credentials.browserEngine || 'chromium';
    const engineAvailable = isBrowserEngineAvailable(engine);
    return this.agentRequest(credentials, `/agents/${credentials.agentId}/heartbeat`, {
      capabilities: {
        chromium: engine === 'chromium' ? engineAvailable : isBrowserEngineAvailable('chromium'),
        firefox: engine === 'firefox' && engineAvailable,
        webkit: engine === 'webkit' && engineAvailable,
        unattended: true,
        case: true,
        suite: true,
        parallel: credentials.maxParallel > 1,
        intercept: true,
        healing: true,
      },
      max_parallel: credentials.maxParallel,
      current_runs: undefined,
    });
  }

  claim(credentials: AgentCredentials): Promise<ClaimResponse> {
    return this.agentRequest(credentials, `/agents/${credentials.agentId}/claim`);
  }

  claimBatch(credentials: AgentCredentials, limit: number): Promise<ClaimBatchResponse> {
    return this.agentRequest(credentials, `/agents/${credentials.agentId}/claim-batch`, { limit });
  }

  appendEvents(credentials: AgentCredentials, runId: number, events: Record<string, unknown>[]): Promise<EventUploadResponse> {
    return this.agentRequest(credentials, `/agents/${credentials.agentId}/runs/${runId}/events`, { events });
  }

  async uploadArtifact(credentials: AgentCredentials, runId: number, artifact: AgentArtifactUpload): Promise<void> {
    const content = artifact.content;
    const created = await this.agentRequest(credentials, `/agents/${credentials.agentId}/runs/${runId}/artifacts/upload-sessions`, {
      kind: artifact.kind,
      filename: artifact.filename,
      content_type: artifact.contentType,
      size_bytes: content.length,
      sha256: createHash('sha256').update(content).digest('hex'),
    });
    const chunkSize = 4 * 1024 * 1024;
    let offset = Number(created.offset || 0);
    while (offset < content.length) {
      const start = offset;
      const end = Math.min(start + chunkSize, content.length);
      try {
        await retryAgentRequest(async () => {
          await uploadAgentChunk(`${credentials.serverUrl}${created.chunk_endpoint}`, {
            method: 'PUT',
            headers: {
              'X-TestMaster-Agent-Token': credentials.token,
              'Content-Range': `bytes ${start}-${end - 1}/${content.length}`,
              'Content-Type': artifact.contentType,
            },
            body: content.subarray(start, end),
          });
        });
        offset = end;
      } catch (error) {
        const progress = await retryAgentRequest(() => this.agentGet(
          credentials,
          `/agents/${credentials.agentId}/runs/${runId}/artifacts/upload-sessions/${created.upload_id}`,
        ));
        if (progress.status !== 'open' || Number(progress.received_bytes) <= start) throw error;
        offset = Number(progress.received_bytes);
      }
    }
    await retryAgentRequest(() => this.agentRequest(
      credentials,
      `/agents/${credentials.agentId}/runs/${runId}/artifacts/upload-sessions/${created.upload_id}/complete`,
    ));
  }

  private agentRequest(credentials: AgentCredentials, path: string, body: object = {}): Promise<any> {
    return fetchJson(`${credentials.serverUrl}/api/ui-automation${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-TestMaster-Agent-Token': credentials.token },
      body: JSON.stringify(body),
    });
  }

  private agentGet(credentials: AgentCredentials, path: string): Promise<any> {
    return fetchJson(`${credentials.serverUrl}/api/ui-automation${path}`, {
      method: 'GET',
      headers: { 'X-TestMaster-Agent-Token': credentials.token },
    });
  }
}

export class AgentEventOutbox {
  private events: Record<string, unknown>[] = [];
  private nextSequence = 1;
  private flushPromise: Promise<void> | null = null;
  private firstFailureAt = 0;
  private stopped = false;
  private fatalError: Error | null = null;
  private deferredTerminal: Record<string, unknown> | null = null;

  constructor(
    private readonly api: AgentApi,
    private readonly credentials: AgentCredentials,
    private readonly runId: number,
    private readonly onFatalDeliveryFailure: (error: Error) => void,
    private readonly persistence?: AgentOutboxStore,
  ) {
    const record = persistence?.load(credentials.agentId).find(item => item.runId === runId);
    if (record) {
      this.events = record.events;
      this.nextSequence = Math.max(
        record.nextSequence,
        ...record.events.map(event => Number(event.sequence) || 0).map(sequence => sequence + 1),
      );
      this.deferredTerminal = record.deferredTerminal;
    }
  }

  enqueue(rawEvent: StepEvent | Record<string, unknown>): void {
    if (this.stopped) return;
    const event = normalizeEvent(rawEvent);
    if (event.type === 'run:finish') {
      this.deferredTerminal = event;
      this.persist();
      return;
    }
    this.events.push({ ...event, sequence: this.nextSequence++, occurred_at: new Date().toISOString() });
    this.persist();
    void this.flush().catch(() => {});
  }

  releaseTerminal(): void {
    if (!this.deferredTerminal || this.stopped) return;
    this.events.push({ ...this.deferredTerminal, sequence: this.nextSequence++, occurred_at: new Date().toISOString() });
    this.deferredTerminal = null;
    this.persist();
    void this.flush().catch(() => {});
  }

  async flush(): Promise<void> {
    if (this.flushPromise) return this.flushPromise;
    this.flushPromise = this.flushLoop().finally(() => { this.flushPromise = null; });
    return this.flushPromise;
  }

  async stopAndFlush(timeoutMs = 10_000): Promise<void> {
    this.releaseTerminal();
    if (this.fatalError) {
      this.stopped = true;
      throw this.fatalError;
    }
    const deadline = Date.now() + timeoutMs;
    while (this.events.length && Date.now() < deadline) {
      await this.flush().catch(() => {});
      if (this.events.length) await delay(Math.min(500, Math.max(1, deadline - Date.now()))).catch(() => {});
    }
    this.stopped = true;
    // The disk queue is intentionally retained when the delivery deadline is
    // exceeded. A later Agent restart retries the exact same sequences.
    this.persist();
  }

  private async flushLoop(): Promise<void> {
    let backoffMs = 500;
    while (this.events.length && !this.stopped) {
      const batch = this.events.slice(0, 50);
      try {
        const response = await this.api.appendEvents(this.credentials, this.runId, batch);
        const terminal = ['passed', 'failed', 'cancelled', 'timed_out', 'infra_error'].includes(response.status);
        const batchFinishesRun = batch.some(event => event.type === 'run:finish');
        if (terminal && !batchFinishesRun) {
          const leaseLost = new Error(`RUN_LEASE_LOST_${response.status.toUpperCase()}`);
          this.fatalError = leaseLost;
          this.onFatalDeliveryFailure(leaseLost);
          throw leaseLost;
        }
        this.events.splice(0, batch.length);
        this.persist();
        this.firstFailureAt = 0;
        backoffMs = 500;
      } catch (error) {
        if (error instanceof Error && error.message.startsWith('RUN_LEASE_LOST_')) throw error;
        if (!this.firstFailureAt) this.firstFailureAt = Date.now();
        if (Date.now() - this.firstFailureAt >= DELIVERY_FAILURE_LIMIT_MS) {
          // The execution result is already on disk.  Do not cancel a long
          // browser run merely because the server is temporarily unreachable.
          // The Agent loop will replay this exact batch after reconnecting.
          this.firstFailureAt = 0;
          throw new Error(`AGENT_EVENT_DELIVERY_DEFERRED: ${boundedText(error)}`);
        }
        await delay(backoffMs);
        backoffMs = Math.min(backoffMs * 2, 5_000);
      }
    }
  }

  private persist(): void {
    if (!this.persistence) return;
    const existing = this.persistence.load(this.credentials.agentId).find(item => item.runId === this.runId);
    const artifacts = existing?.artifacts || [];
    if (!this.events.length && !this.deferredTerminal && !artifacts.length) {
      this.persistence.remove(this.credentials.agentId, this.runId);
      return;
    }
    this.persistence.save(this.credentials.agentId, {
      runId: this.runId,
      nextSequence: this.nextSequence,
      events: this.events,
      deferredTerminal: this.deferredTerminal,
      artifacts,
      updatedAt: new Date().toISOString(),
    });
  }
}

function normalizeEvent(raw: StepEvent | Record<string, unknown>): Record<string, unknown> {
  const event = { ...raw } as Record<string, unknown>;
  if (event.type === 'network') {
    event.httpStatus = event.status;
    delete event.status;
  }
  if (event.type === 'run:paused') {
    return { type: 'log', level: 'info', message: 'Agent execution paused at a breakpoint' };
  }
  if (event.type === 'run:resumed') {
    return { type: 'log', level: 'info', message: 'Agent execution resumed' };
  }
  return event;
}

function environmentFromPlan(value: AgentEnvironment | null | undefined): EnvironmentConfig | null {
  if (!value) return null;
  return {
    baseUrl: String(value.base_url ?? value.baseUrl ?? ''),
    variables: value.variables && typeof value.variables === 'object' ? value.variables : {},
    secretKeys: Array.isArray(value.secret_keys) ? value.secret_keys : Array.isArray(value.secretKeys) ? value.secretKeys : [],
  };
}

export class DesktopAgentService {
  private readonly store: AgentCredentialStore;
  private readonly api: AgentApi;
  private readonly createEngine: () => AgentExecutionEngine;
  private readonly loadAuthState: (id: string) => object;
  private readonly onStatus: (status: DesktopAgentStatus) => void;
  private readonly desktopVersion: string;
  private readonly heartbeatIntervalMs: number;
  private readonly claimIntervalMs: number;
  private readonly runHeartbeatIntervalMs: number;
  private readonly artifactRootDir?: string;
  private readonly outboxStore: AgentOutboxStore;
  private credentials: AgentCredentials | null = null;
  private loopPromise: Promise<void> | null = null;
  private loopAbort: AbortController | null = null;
  private activeEngine: AgentExecutionEngine | null = null;
  private readonly activeWorkers = new Map<number, { engine: AgentExecutionEngine; promise: Promise<void> }>();
  private status: DesktopAgentStatus = {
    state: 'unregistered', registered: false, enabled: false, agentId: null, agentKey: null,
    name: null, serverUrl: null, authStateId: null, headless: true, maxParallel: 1, browserEngine: 'chromium',
    activeRunId: null, activeRunIds: [],
    lastHeartbeatAt: null, lastClaimAt: null, lastError: null, retryInMs: null,
  };

  constructor(dependencies: DesktopAgentDependencies = {}) {
    this.store = dependencies.store ?? new SecureAgentCredentialStore();
    this.api = dependencies.api ?? new HttpAgentApi();
    this.createEngine = dependencies.createEngine ?? (() => new CaseExecutionEngine());
    this.loadAuthState = dependencies.loadAuthState ?? (() => { throw new Error('AUTH_STATE_LOADER_NOT_CONFIGURED'); });
    this.onStatus = dependencies.onStatus ?? (() => {});
    this.desktopVersion = dependencies.desktopVersion ?? 'unknown';
    this.heartbeatIntervalMs = dependencies.heartbeatIntervalMs ?? DEFAULT_HEARTBEAT_MS;
    this.claimIntervalMs = dependencies.claimIntervalMs ?? DEFAULT_CLAIM_MS;
    this.runHeartbeatIntervalMs = dependencies.runHeartbeatIntervalMs ?? DEFAULT_RUN_HEARTBEAT_MS;
    this.artifactRootDir = dependencies.artifactRootDir;
    this.outboxStore = dependencies.outboxStore ?? new FileAgentOutboxStore();
  }

  initialize(): DesktopAgentStatus {
    try {
      this.credentials = this.store.load();
      if (!this.credentials) return this.publish({ state: 'unregistered', registered: false, enabled: false });
      this.syncCredentialStatus();
      if (this.credentials.enabled) void this.startLoop();
      return this.getStatus();
    } catch (error) {
      return this.publish({ state: 'error', registered: false, enabled: false, lastError: boundedText(error) });
    }
  }

  getStatus(): DesktopAgentStatus {
    return { ...this.status };
  }

  async register(input: AgentRegistrationInput): Promise<DesktopAgentStatus> {
    const serverUrl = normalizeServerUrl(input.serverUrl);
    const name = String(input.name || '').trim().slice(0, 200);
    if (!name) throw new Error('AGENT_NAME_REQUIRED');
    if (!input.accessToken) throw new Error('LOGIN_REQUIRED');
    const maxParallel = Math.max(1, Math.min(16, Number(input.maxParallel || 1)));
    const browserEngine = input.browserEngine === 'firefox' || input.browserEngine === 'webkit'
      ? input.browserEngine
      : 'chromium';
    await this.stopLoop(false);
    this.publish({ state: 'starting', lastError: null, retryInMs: null });
    let registered: Record<string, any>;
    try {
      registered = await this.api.register({ ...input, serverUrl, name, maxParallel, browserEngine }, {
        hostname: os.hostname(),
        os_version: `${process.platform} ${os.release()}`,
        desktop_version: this.desktopVersion,
      });
    } catch (error) {
      this.publish({ state: 'error', lastError: boundedText(error), retryInMs: null });
      throw error;
    }
    if (!Number.isInteger(registered.id) || typeof registered.bootstrap_token !== 'string') {
      throw new Error('AGENT_REGISTRATION_RESPONSE_INVALID');
    }
    const now = new Date().toISOString();
    this.credentials = {
      serverUrl,
      agentId: registered.id,
      agentKey: String(registered.agent_key || ''),
      projectId: Number.isInteger(registered.project_id) ? Number(registered.project_id) : null,
      name,
      token: registered.bootstrap_token,
      authStateId: input.authStateId || null,
      enabled: true,
      headless: input.headless !== false,
      maxParallel,
      browserEngine,
      registeredAt: now,
      updatedAt: now,
    };
    this.store.save(this.credentials);
    this.syncCredentialStatus();
    void this.startLoop();
    return this.getStatus();
  }

  async enable(): Promise<DesktopAgentStatus> {
    if (!this.credentials) throw new Error('AGENT_NOT_REGISTERED');
    this.credentials = { ...this.credentials, enabled: true, updatedAt: new Date().toISOString() };
    this.store.save(this.credentials);
    this.syncCredentialStatus();
    void this.startLoop();
    return this.getStatus();
  }

  async disable(): Promise<DesktopAgentStatus> {
    if (!this.credentials) return this.getStatus();
    this.credentials = { ...this.credentials, enabled: false, updatedAt: new Date().toISOString() };
    this.store.save(this.credentials);
    await this.stopLoop(false);
    return this.publish({ state: 'disabled', enabled: false, activeRunId: null, retryInMs: null });
  }

  async remove(): Promise<DesktopAgentStatus> {
    await this.stopLoop(false);
    this.store.clear();
    if (this.credentials) this.outboxStore.clear(this.credentials.agentId);
    this.credentials = null;
    this.status = {
      state: 'unregistered', registered: false, enabled: false, agentId: null, agentKey: null,
      name: null, serverUrl: null, authStateId: null, headless: true, maxParallel: 1, browserEngine: 'chromium',
      activeRunId: null, activeRunIds: [],
      lastHeartbeatAt: null, lastClaimAt: null, lastError: null, retryInMs: null,
    };
    this.onStatus(this.getStatus());
    return this.getStatus();
  }

  async shutdown(): Promise<void> {
    await this.stopLoop(false);
  }

  private async startLoop(): Promise<void> {
    if (this.loopPromise || !this.credentials?.enabled) return;
    this.loopAbort = new AbortController();
    this.publish({ state: 'starting', enabled: true, lastError: null, retryInMs: null });
    this.loopPromise = this.runLoop(this.loopAbort.signal).finally(() => {
      this.loopPromise = null;
      this.loopAbort = null;
    });
    return this.loopPromise;
  }

  private async stopLoop(disable: boolean): Promise<void> {
    if (disable && this.credentials) this.credentials.enabled = false;
    this.publish({ state: this.credentials ? 'stopping' : 'unregistered', retryInMs: null });
    this.loopAbort?.abort();
    if (this.activeEngine) await this.activeEngine.cancel().catch(() => {});
    for (const worker of this.activeWorkers.values()) {
      await worker.engine.cancel().catch(() => {});
    }
    // Shared deadline: loop + workers must finish within 15s total (fits 25s shutdown budget).
    const deadline = Date.now() + 15_000;
    const loop = this.loopPromise;
    if (loop) {
      const remaining = Math.max(0, deadline - Date.now());
      await Promise.race([loop.catch(() => {}), delay(remaining).catch(() => {})]);
      // Prevent permanent false-online: clear even if the loop hung past the budget.
      this.loopPromise = null;
      this.loopAbort = null;
    }
    const pending = [...this.activeWorkers.values()].map(item => item.promise);
    if (pending.length) {
      const remaining = Math.max(0, deadline - Date.now());
      await Promise.race([Promise.allSettled(pending), delay(remaining).catch(() => {})]);
    }
    // Drop slots that did not finish so a later startLoop can claim again.
    this.activeWorkers.clear();
    this.activeEngine = null;
  }

  private freeSlots(): number {
    const maxParallel = Math.max(1, this.credentials?.maxParallel || 1);
    return Math.max(0, maxParallel - this.activeWorkers.size);
  }

  private publishActiveRuns(): void {
    const ids = [...this.activeWorkers.keys()];
    this.publish({
      activeRunIds: ids,
      activeRunId: ids[0] ?? null,
      state: ids.length ? 'running' : (this.credentials?.enabled ? 'online' : this.status.state),
    });
  }

  private async runLoop(signal: AbortSignal): Promise<void> {
    let backoffMs = 1_000;
    let lastHeartbeat = 0;
    while (!signal.aborted && this.credentials?.enabled) {
      const credentials = this.credentials;
      try {
        if (await this.flushPersistedOutboxes(credentials)) {
          this.publish({ lastError: null, retryInMs: null });
        }
        if (Date.now() - lastHeartbeat >= this.heartbeatIntervalMs) {
          const response = await this.api.heartbeat(credentials);
          lastHeartbeat = Date.now();
          const cancelIds = response?.cancel_run_ids || [];
          for (const runId of cancelIds) {
            const worker = this.activeWorkers.get(runId);
            if (worker) await worker.engine.cancel().catch(() => {});
          }
          this.publish({
            state: this.activeWorkers.size ? 'running' : 'online',
            lastHeartbeatAt: new Date().toISOString(),
            lastError: null,
            retryInMs: null,
          });
        }

        const slots = this.freeSlots();
        if (slots > 0) {
          let claimed: Array<{ run: AgentRun; plan: CasePlan | SuitePlan }> = [];
          if (this.api.claimBatch && slots > 1) {
            const batch = await this.api.claimBatch(credentials, slots);
            const rawItems = batch.items || [];
            claimed = rawItems.filter(item => item?.run && item?.plan) as Array<{ run: AgentRun; plan: CasePlan | SuitePlan }>;
            // Runs without a plan must not stay pending forever on the server.
            for (const item of rawItems) {
              if (item?.run && !item?.plan) {
                await this.api.appendEvents(credentials, item.run.id, [{
                  type: 'run:finish',
                  status: 'infra_error',
                  error: 'CLAIM_MISSING_PLAN',
                  passedSteps: 0,
                  failedSteps: 0,
                }]).catch(() => {});
              }
            }
          } else {
            const claim = await this.api.claim(credentials);
            if (claim.run && claim.plan) {
              claimed = [{ run: claim.run, plan: claim.plan }];
            } else if (claim.run && !claim.plan) {
              await this.api.appendEvents(credentials, claim.run.id, [{
                type: 'run:finish',
                status: 'infra_error',
                error: 'CLAIM_MISSING_PLAN',
                passedSteps: 0,
                failedSteps: 0,
              }]).catch(() => {});
            }
          }
          this.publish({ lastClaimAt: new Date().toISOString() });
          backoffMs = 1_000;
          for (const item of claimed) {
            if (this.activeWorkers.has(item.run.id) || this.freeSlots() <= 0) continue;
            // Reserve the slot immediately so claim loops respect maxParallel.
            // Use a cancelable stub engine; real engine is bound inside executeClaim.
            const stubEngine: AgentExecutionEngine = {
              cancel: async () => {},
              execute: async () => {
                throw new Error('STUB_ENGINE');
              },
            } as unknown as AgentExecutionEngine;
            const reservation: { engine: AgentExecutionEngine; promise: Promise<void> } = {
              engine: stubEngine,
              promise: Promise.resolve(),
            };
            this.activeWorkers.set(item.run.id, reservation);
            this.publishActiveRuns();
            reservation.promise = this.executeClaim(credentials, item.run, item.plan, signal, (engine) => {
              reservation.engine = engine;
            })
              .catch(() => {})
              .finally(() => {
                this.activeWorkers.delete(item.run.id);
                this.publishActiveRuns();
              });
          }
          if (claimed.length) {
            lastHeartbeat = 0;
            continue;
          }
        }
        await delay(this.claimIntervalMs, signal);
      } catch (error: any) {
        if (signal.aborted || error?.message === 'ABORTED') break;
        const unauthorized = error?.status === 401;
        this.publish({
          state: unauthorized ? 'error' : 'offline',
          lastError: unauthorized ? 'Agent 凭据已失效，请重新注册' : boundedText(error),
          retryInMs: unauthorized ? null : backoffMs,
        });
        if (unauthorized) break;
        await delay(backoffMs, signal).catch(() => {});
        backoffMs = Math.min(backoffMs * 2, 30_000);
      }
    }
    if (this.credentials && !this.credentials.enabled) this.publish({ state: 'disabled', enabled: false });
  }

  private async flushPersistedOutboxes(credentials: AgentCredentials): Promise<boolean> {
    const records = this.outboxStore.load(credentials.agentId);
    let deliveredAny = false;
    for (const record of records) {
      const remainingArtifacts = await this.flushPersistedArtifacts(credentials, record);
      const events = [...record.events];
      let nextSequence = Math.max(record.nextSequence || 1, ...events.map(event => Number(event.sequence) + 1 || 1));
      if (record.deferredTerminal) {
        events.push({ ...record.deferredTerminal, sequence: nextSequence++, occurred_at: new Date().toISOString() });
      }
      while (events.length) {
        const batch = events.slice(0, 50);
        const response = await this.api.appendEvents(credentials, record.runId, batch);
        const terminal = ['passed', 'failed', 'cancelled', 'timed_out', 'infra_error'].includes(response.status);
        if (terminal && !batch.some(event => event.type === 'run:finish')) {
          throw new Error(`PERSISTED_OUTBOX_CONFLICT_${response.status.toUpperCase()}`);
        }
        events.splice(0, batch.length);
        this.outboxStore.save(credentials.agentId, {
          runId: record.runId,
          nextSequence,
          events,
          deferredTerminal: null,
          artifacts: remainingArtifacts,
          updatedAt: new Date().toISOString(),
        });
        deliveredAny = true;
      }
      if (remainingArtifacts.length) {
        this.outboxStore.save(credentials.agentId, {
          runId: record.runId,
          nextSequence,
          events: [],
          deferredTerminal: null,
          artifacts: remainingArtifacts,
          updatedAt: new Date().toISOString(),
        });
      } else {
        this.outboxStore.remove(credentials.agentId, record.runId);
      }
    }
    return deliveredAny;
  }

  private async flushPersistedArtifacts(
    credentials: AgentCredentials,
    record: AgentOutboxRecord,
  ): Promise<AgentOutboxArtifact[]> {
    if (!record.artifacts.length || !this.api.uploadArtifact) return record.artifacts;
    const remaining: AgentOutboxArtifact[] = [];
    for (const artifact of record.artifacts) {
      try {
        const fileInfo = await stat(artifact.path);
        if (!fileInfo.isFile() || fileInfo.size <= 0) throw new Error('ARTIFACT_FILE_UNAVAILABLE');
        await this.api.uploadArtifact(credentials, record.runId, {
          kind: artifact.kind,
          filename: artifact.filename,
          contentType: artifact.contentType,
          content: await readFile(artifact.path),
        });
      } catch (error) {
        remaining.push(artifact);
        this.publish({ lastError: `离线产物待上传：${boundedText(error)}` });
      }
    }
    return remaining;
  }

  private async executeClaim(
    credentials: AgentCredentials,
    run: AgentRun,
    plan: CasePlan | SuitePlan,
    signal: AbortSignal,
    onEngine?: (engine: AgentExecutionEngine) => void,
  ): Promise<void> {
    this.publish({ state: 'running', activeRunId: run.id, lastError: null, retryInMs: null });
    let deliveryFailure: Error | null = null;
    let localEngine: AgentExecutionEngine | null = null;
    const bindEngine = (engine: AgentExecutionEngine) => {
      localEngine = engine;
      this.activeEngine = engine;
      onEngine?.(engine);
    };
    const outbox = new AgentEventOutbox(this.api, credentials, run.id, (error) => {
      deliveryFailure = error;
      void localEngine?.cancel();
    }, this.outboxStore);
    let heartbeatInFlight = false;
    const pollCancellation = async () => {
      if (heartbeatInFlight) return;
      heartbeatInFlight = true;
      try {
        const response = await this.api.heartbeat(credentials);
        if (response?.cancel_run_ids?.includes(run.id)) {
          await localEngine?.cancel();
        }
      } catch (error) {
        // Event delivery has its own bounded retry/failure policy. Keep a
        // transient control-plane outage from immediately killing a test run.
        this.publish({ lastError: boundedText(error) });
      } finally {
        heartbeatInFlight = false;
      }
    };
    const keepalive = setInterval(() => {
      outbox.enqueue({ type: 'log', level: 'info', message: 'Agent execution heartbeat' });
      void pollCancellation();
    }, this.runHeartbeatIntervalMs);
    try {
      const storageState = credentials.authStateId ? this.loadAuthState(credentials.authStateId) : null;
      const projectId = Number(run.project_id || run.user_id || 1) || 1;
      const networkRules = await this.loadNetworkRules(credentials, projectId, plan);
      const options: RunOptions = {
        headless: credentials.headless,
        screenshotsOnFailure: true,
        traceOnFailure: true,
        videoOnFailure: false,
        debugMode: false,
        storageState,
        artifactRootDir: this.artifactRootDir,
        browserEngine: credentials.browserEngine || 'chromium',
        healingEndpoint: `${credentials.serverUrl}/api/ui-automation/agents/${credentials.agentId}/healing/heal`,
        // Prefer run.project_id; fall back to run owner workspace.
        projectId,
        runId: run.id,
        accessToken: credentials.token,
        agentToken: credentials.token,
        agentId: credentials.agentId,
        networkRules,
      };
      const results = plan.kind === 'case'
        ? [await this.executeCase(plan.snapshot, environmentFromPlan(plan.environment), options, outbox, signal, true, bindEngine)]
        : await this.executeSuite(plan, options, outbox, signal, bindEngine);
      await this.uploadRunArtifacts(credentials, run.id, results);
      if (deliveryFailure) throw deliveryFailure;
    } catch (error) {
      if (!deliveryFailure) {
        outbox.enqueue({
          type: 'run:finish',
          status: signal.aborted ? 'cancelled' : 'infra_error',
          passedSteps: 0,
          failedSteps: 0,
          error: boundedText(error),
        } as Record<string, unknown>);
      }
      this.publish({ lastError: boundedText(error) });
    } finally {
      clearInterval(keepalive);
      outbox.releaseTerminal();
      await outbox.stopAndFlush(10_000).catch((error) => this.publish({ lastError: boundedText(error) }));
      if (this.activeEngine === localEngine) this.activeEngine = null;
      this.publishActiveRuns();
    }
  }

  private async loadNetworkRules(
    credentials: AgentCredentials,
    projectId: number,
    plan: any,
  ): Promise<any[]> {
    try {
      const targetType = plan?.kind === 'suite' ? 'ui_suite' : 'ui_case';
      const targetId = Number(plan?.caseId || plan?.suiteId || plan?.snapshot?.case_id || 0);
      if (!targetId) return [];
      const url = `${credentials.serverUrl}/api/feature-upgrades/network/rules/for-target?project_id=${projectId}&target_type=${encodeURIComponent(targetType)}&target_id=${targetId}`;
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${credentials.token}`,
          'X-TestMaster-Agent-Token': credentials.token,
        },
      });
      if (!response.ok) return [];
      const data = await response.json() as { agent_payload?: any[] };
      return Array.isArray(data.agent_payload) ? data.agent_payload : [];
    } catch {
      return [];
    }
  }

  private async executeCase(
    snapshot: CaseSnapshot,
    environment: EnvironmentConfig | null,
    options: RunOptions,
    outbox: AgentEventOutbox,
    signal: AbortSignal,
    includeRunEvents: boolean,
    onEngine?: (engine: AgentExecutionEngine) => void,
  ): Promise<RunResult> {
    if (signal.aborted) throw new Error('AGENT_STOPPING');
    const engine = this.createEngine();
    this.activeEngine = engine;
    onEngine?.(engine);
    const onAbort = () => { void engine.cancel(); };
    signal.addEventListener('abort', onAbort, { once: true });
    try {
      return await engine.execute(snapshot, environment, options, event => {
        if (includeRunEvents || (event.type !== 'run:start' && event.type !== 'run:finish')) outbox.enqueue(event);
      });
    } finally {
      signal.removeEventListener('abort', onAbort);
      if (this.activeEngine === engine) this.activeEngine = null;
    }
  }

  private async executeSuite(
    suite: SuitePlan,
    options: RunOptions,
    outbox: AgentEventOutbox,
    signal: AbortSignal,
    onEngine?: (engine: AgentExecutionEngine) => void,
  ): Promise<RunResult[]> {
    const startedAt = Date.now();
    const entries = Array.isArray(suite.plan.entries) ? suite.plan.entries : [];
    const totalSteps = entries.reduce((sum, entry) => sum + (entry.snapshot.steps?.filter(step => step.enabled !== false).length || 0), 0);
    outbox.enqueue({ type: 'run:start', totalSteps });
    let passedSteps = 0;
    let failedSteps = 0;
    let status: RunResult['status'] = 'passed';
    const baseEnvironment = environmentFromPlan(suite.environment);
    const results: RunResult[] = [];
    for (let index = 0; index < entries.length; index += 1) {
      if (signal.aborted) { status = 'cancelled'; break; }
      const entry = entries[index];
      const environment: EnvironmentConfig | null = {
        baseUrl: baseEnvironment?.baseUrl || entry.snapshot.base_url || '',
        variables: { ...(baseEnvironment?.variables || {}), ...(entry.variables || {}) },
        secretKeys: baseEnvironment?.secretKeys || [],
      };
      const result = await this.executeCase(entry.snapshot, environment, options, outbox, signal, false, onEngine);
      results.push(result);
      passedSteps += result.passedSteps;
      failedSteps += result.failedSteps;
      if (result.status !== 'passed') status = result.status;
      if (result.status !== 'passed' && suite.plan.stop_on_first_failure) {
        for (const remaining of entries.slice(index + 1)) {
          for (const step of remaining.snapshot.steps || []) {
            if (step.enabled !== false) outbox.enqueue({ type: 'step:skip', stepId: step.id, reason: '套件已在首个失败后停止' });
          }
        }
        break;
      }
    }
    outbox.enqueue({
      type: 'run:finish',
      status,
      passedSteps,
      failedSteps,
      durationMs: Date.now() - startedAt,
      shardId: (suite.plan as any)?.shard_id ?? (suite as any)?.shard_id ?? null,
      caseIds: entries.map((entry: any) => entry?.case_id ?? entry?.caseId).filter(Boolean),
      passedCases: results.filter((r) => r.status === 'passed').length,
      failedCases: results.filter((r) => r.status !== 'passed').length,
    });
    return results;
  }

  private async uploadRunArtifacts(credentials: AgentCredentials, runId: number, results: RunResult[]): Promise<void> {
    if (!this.api.uploadArtifact) return;
    const paths = results.flatMap(result => [
      ...(result.stepResults || []).map(item => item.screenshotPath),
      result.tracePath,
      result.videoPath,
    ]).filter((value): value is string => Boolean(value));
    for (const filePath of [...new Set(paths)]) {
      const extension = path.extname(filePath).toLowerCase();
      const kind: AgentArtifactUpload['kind'] = extension === '.zip' ? 'trace' : extension === '.webm' ? 'video' : 'screenshot';
      const contentType = kind === 'trace' ? 'application/zip' : kind === 'video' ? 'video/webm' : 'image/png';
      try {
        const fileInfo = await stat(filePath);
        if (!fileInfo.isFile() || fileInfo.size <= 0) continue;
        await this.api.uploadArtifact(credentials, runId, {
          kind,
          filename: path.basename(filePath),
          contentType,
          content: await readFile(filePath),
        });
      } catch (error) {
        // An artifact failure must be visible in the durable run log, but it
        // should not convert an otherwise valid browser result into a false fail.
        this.publish({ lastError: `运行产物上传失败：${boundedText(error)}` });
        this.enqueueArtifact(credentials, runId, { kind, filename: path.basename(filePath), contentType, path: filePath });
      }
    }
  }

  private enqueueArtifact(credentials: AgentCredentials, runId: number, artifact: AgentOutboxArtifact): void {
    const existing = this.outboxStore.load(credentials.agentId).find(item => item.runId === runId);
    const artifacts = [...(existing?.artifacts || [])];
    if (!artifacts.some(item => item.path === artifact.path && item.kind === artifact.kind)) artifacts.push(artifact);
    this.outboxStore.save(credentials.agentId, {
      runId,
      nextSequence: existing?.nextSequence || 1,
      events: existing?.events || [],
      deferredTerminal: existing?.deferredTerminal || null,
      artifacts,
      updatedAt: new Date().toISOString(),
    });
  }

  private syncCredentialStatus(): void {
    const credentials = this.credentials;
    if (!credentials) return;
    this.publish({
      state: credentials.enabled ? 'starting' : 'disabled',
      registered: true,
      enabled: credentials.enabled,
      agentId: credentials.agentId,
      agentKey: credentials.agentKey,
      name: credentials.name,
      serverUrl: credentials.serverUrl,
      authStateId: credentials.authStateId,
      headless: credentials.headless,
      maxParallel: credentials.maxParallel || 1,
      browserEngine: credentials.browserEngine || 'chromium',
      lastError: null,
    });
  }

  private publish(update: Partial<DesktopAgentStatus>): DesktopAgentStatus {
    this.status = { ...this.status, ...update };
    this.onStatus(this.getStatus());
    return this.getStatus();
  }
}
