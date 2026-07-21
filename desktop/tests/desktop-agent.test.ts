import { afterEach, describe, expect, it } from 'vitest';
import { mkdtemp, rm, writeFile } from 'fs/promises';
import { tmpdir } from 'os';
import { join } from 'path';
import { AgentCredentialStore, AgentCredentials } from '../src/main/agent-state-store';
import { DesktopAgentService } from '../src/main/desktop-agent-service';
import { CaseSnapshot, EnvironmentConfig, RunOptions, RunResult, StepEvent } from '../src/worker/execution-engine';

class MemoryStore implements AgentCredentialStore {
  value: AgentCredentials | null = null;
  load(): AgentCredentials | null { return this.value ? { ...this.value } : null; }
  save(value: AgentCredentials): void { this.value = { ...value }; }
  clear(): void { this.value = null; }
}

class FakeEngine {
  cancelled = false;
  constructor(
    private readonly result: RunResult,
    private readonly environments: Array<EnvironmentConfig | null>,
    private readonly executionDelayMs = 0,
  ) {}
  async execute(
    snapshot: CaseSnapshot,
    environment: EnvironmentConfig | null,
    _options: RunOptions,
    onEvent: (event: StepEvent) => void,
  ): Promise<RunResult> {
    this.environments.push(environment);
    onEvent({ type: 'run:start', totalSteps: snapshot.steps.length });
    const stepId = snapshot.steps[0]?.id || 'none';
    onEvent({ type: 'step:start', stepId, stepName: 'Open', stepType: 'goto' });
    if (this.executionDelayMs) await new Promise(resolve => setTimeout(resolve, this.executionDelayMs));
    if (this.result.status === 'passed') onEvent({ type: 'step:pass', stepId, durationMs: 5 });
    else onEvent({ type: 'step:fail', stepId, durationMs: 5, error: 'expected failure' });
    onEvent({
      type: 'run:finish', status: this.cancelled ? 'cancelled' : this.result.status,
      passedSteps: this.result.passedSteps, failedSteps: this.result.failedSteps, durationMs: 5,
    });
    return this.cancelled ? { ...this.result, status: 'cancelled' } : this.result;
  }
  async cancel(): Promise<void> { this.cancelled = true; }
}

const snapshot = (caseId: number, stepId: string): CaseSnapshot => ({
  case_id: caseId,
  name: `case-${caseId}`,
  base_url: 'https://app.example.test',
  default_timeout_ms: 1_000,
  navigation_timeout_ms: 1_000,
  steps: [{
    id: stepId, order: 10, name: 'Open', type: 'goto', enabled: true, breakpoint: false,
    locator: null, input: { url: '/' }, timeout_ms: 1_000, retry: { count: 0, delay_ms: 0 },
    continue_on_failure: false, screenshot: 'never', condition: null, children: [],
  }],
});

const passedResult = (): RunResult => ({
  status: 'passed', totalSteps: 1, passedSteps: 1, failedSteps: 0, durationMs: 5,
  stepResults: [], tracePath: null, videoPath: null,
});

async function waitFor(predicate: () => boolean, timeoutMs = 2_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (!predicate() && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 10));
  if (!predicate()) throw new Error('Timed out waiting for Agent state');
}

const services: DesktopAgentService[] = [];
afterEach(async () => {
  await Promise.all(services.splice(0).map(service => service.shutdown()));
});

describe('Desktop Agent', () => {
  it('registers with the signed-in user but persists only the Agent credential', async () => {
    const store = new MemoryStore();
    const uploaded: any[][] = [];
    let claimed = false;
    let registrationAccessToken = '';
    const environments: Array<EnvironmentConfig | null> = [];
    const api = {
      async register(input: any) {
        registrationAccessToken = input.accessToken;
        return { id: 7, agent_key: 'agent-key-7', bootstrap_token: 'agent-bootstrap-token-1234567890' };
      },
      async heartbeat() {},
      async claim() {
        if (claimed) return { run: null };
        claimed = true;
        return {
          run: { id: 91, status: 'assigned' },
          plan: { kind: 'case', run_id: 91, snapshot: snapshot(1, 'open-1'), environment: { base_url: 'https://runtime.example.test', variables: { USER: 'qa' } } },
        };
      },
      async appendEvents(_credentials: AgentCredentials, _runId: number, events: any[]) {
        uploaded.push(events);
        return { accepted: events.length, ignored: 0, last_sequence: events.at(-1).sequence, status: 'running' };
      },
    };
    const service = new DesktopAgentService({
      store, api, createEngine: () => new FakeEngine(passedResult(), environments),
      loadAuthState: () => ({ cookies: [] }), claimIntervalMs: 5, heartbeatIntervalMs: 20,
    });
    services.push(service);

    await service.register({
      serverUrl: 'https://testmaster.example.test/', accessToken: 'signed-in-user-token', name: 'QA runner',
      authStateId: '00000000-0000-0000-0000-000000000001', headless: true,
    });
    await waitFor(() => uploaded.flat().some(event => event.type === 'run:finish'));
    await service.disable();

    expect(registrationAccessToken).toBe('signed-in-user-token');
    expect(store.value?.token).toBe('agent-bootstrap-token-1234567890');
    expect(JSON.stringify(store.value)).not.toContain('signed-in-user-token');
    expect(store.value?.serverUrl).toBe('https://testmaster.example.test');
    expect(environments[0]).toMatchObject({ baseUrl: 'https://runtime.example.test', variables: { USER: 'qa' } });
    const events = uploaded.flat();
    expect(events.map(event => event.sequence)).toEqual(events.map((_event, index) => index + 1));
    expect(events.map(event => event.type)).toEqual(expect.arrayContaining(['run:start', 'step:start', 'step:pass', 'run:finish']));
    expect(service.getStatus().state).toBe('disabled');
  });

  it('executes every suite entry through the case engine and emits one run envelope', async () => {
    const store = new MemoryStore();
    const uploaded: any[][] = [];
    const environments: Array<EnvironmentConfig | null> = [];
    const engineResults = [passedResult(), passedResult()];
    let claimed = false;
    const api = {
      async register() { return { id: 8, agent_key: 'agent-key-8', bootstrap_token: 'agent-bootstrap-token-abcdefghij' }; },
      async heartbeat() {},
      async claim() {
        if (claimed) return { run: null };
        claimed = true;
        return {
          run: { id: 92, status: 'assigned' },
          plan: {
            kind: 'suite', run_id: 92,
            environment: { base_url: 'https://suite.example.test', variables: { SHARED: 'base' }, secret_keys: ['PASSWORD'] },
            plan: { stop_on_first_failure: false, entries: [
              { snapshot: snapshot(2, 'open-2'), variables: { ROW: 'one' } },
              { snapshot: snapshot(3, 'open-3'), variables: { ROW: 'two' } },
            ] },
          },
        };
      },
      async appendEvents(_credentials: AgentCredentials, _runId: number, events: any[]) {
        uploaded.push(events);
        return { accepted: events.length, ignored: 0, last_sequence: events.at(-1).sequence, status: 'running' };
      },
    };
    const service = new DesktopAgentService({
      store, api, createEngine: () => new FakeEngine(engineResults.shift()!, environments),
      loadAuthState: () => ({}), claimIntervalMs: 5,
    });
    services.push(service);
    await service.register({ serverUrl: 'https://testmaster.example.test', accessToken: 'user-token', name: 'Suite runner' });
    await waitFor(() => uploaded.flat().some(event => event.type === 'run:finish'));
    await service.disable();

    const events = uploaded.flat();
    expect(events.filter(event => event.type === 'run:start')).toHaveLength(1);
    expect(events.filter(event => event.type === 'run:finish')).toHaveLength(1);
    expect(events.find(event => event.type === 'run:start').totalSteps).toBe(2);
    expect(events.find(event => event.type === 'run:finish')).toMatchObject({ status: 'passed', passedSteps: 2, failedSteps: 0 });
    expect(environments).toHaveLength(2);
    expect(environments[0]?.variables).toEqual({ SHARED: 'base', ROW: 'one' });
    expect(environments[1]?.variables).toEqual({ SHARED: 'base', ROW: 'two' });
    expect(environments[0]?.secretKeys).toEqual(['PASSWORD']);
  });

  it('sends run heartbeat events while a long case is quiet', async () => {
    const store = new MemoryStore();
    const uploaded: any[][] = [];
    let claimed = false;
    const api = {
      async register() { return { id: 9, agent_key: 'agent-key-9', bootstrap_token: 'agent-bootstrap-token-klmnopqrst' }; },
      async heartbeat() {},
      async claim() {
        if (claimed) return { run: null };
        claimed = true;
        return { run: { id: 93, status: 'assigned' }, plan: { kind: 'case', run_id: 93, snapshot: snapshot(4, 'slow-step') } };
      },
      async appendEvents(_credentials: AgentCredentials, _runId: number, events: any[]) {
        uploaded.push(events);
        return { accepted: events.length, ignored: 0, last_sequence: events.at(-1).sequence, status: 'running' };
      },
    };
    const service = new DesktopAgentService({
      store, api, createEngine: () => new FakeEngine(passedResult(), [], 35),
      loadAuthState: () => ({}), claimIntervalMs: 5, runHeartbeatIntervalMs: 5,
    });
    services.push(service);
    await service.register({ serverUrl: 'https://testmaster.example.test', accessToken: 'user-token', name: 'Heartbeat runner' });
    await waitFor(() => uploaded.flat().some(event => event.type === 'run:finish'));
    await service.disable();
    expect(uploaded.flat().some(event => event.type === 'log' && event.message === 'Agent execution heartbeat')).toBe(true);
  });

  it('stops an active browser execution when the server returns a cancellation directive', async () => {
    const store = new MemoryStore();
    const uploaded: any[][] = [];
    let claimed = false;
    let heartbeatCalls = 0;
    const api = {
      async register() { return { id: 11, agent_key: 'agent-key-11', bootstrap_token: 'agent-bootstrap-token-cancelled' }; },
      async heartbeat() {
        heartbeatCalls += 1;
        return heartbeatCalls >= 3 ? { cancel_run_ids: [95] } : { cancel_run_ids: [] };
      },
      async claim() {
        if (claimed) return { run: null };
        claimed = true;
        return { run: { id: 95, status: 'assigned' }, plan: { kind: 'case', run_id: 95, snapshot: snapshot(6, 'cancel-step') } };
      },
      async appendEvents(_credentials: AgentCredentials, _runId: number, events: any[]) {
        uploaded.push(events);
        return { accepted: events.length, ignored: 0, last_sequence: events.at(-1).sequence, status: 'running' };
      },
    };
    const service = new DesktopAgentService({
      store, api, createEngine: () => new FakeEngine(passedResult(), [], 60),
      loadAuthState: () => ({}), claimIntervalMs: 5, heartbeatIntervalMs: 5, runHeartbeatIntervalMs: 5,
    });
    services.push(service);
    await service.register({ serverUrl: 'https://testmaster.example.test', accessToken: 'user-token', name: 'Cancellation runner' });
    await waitFor(() => uploaded.flat().some(event => event.type === 'run:finish'));
    await service.disable();

    expect(heartbeatCalls).toBeGreaterThanOrEqual(3);
    expect(uploaded.flat().find(event => event.type === 'run:finish')).toMatchObject({ status: 'cancelled' });
  });

  it('uploads generated artifacts before delivering the terminal event', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'testmaster-agent-'));
    const screenshotPath = join(directory, 'failure.png');
    await writeFile(screenshotPath, 'png-content');
    const store = new MemoryStore();
    const order: string[] = [];
    let claimed = false;
    const result = { ...passedResult(), stepResults: [{ screenshotPath }], tracePath: null, videoPath: null };
    const api = {
      async register() { return { id: 12, agent_key: 'agent-key-12', bootstrap_token: 'agent-bootstrap-token-artifact' }; },
      async heartbeat() { return { cancel_run_ids: [] }; },
      async claim() {
        if (claimed) return { run: null };
        claimed = true;
        return { run: { id: 96, status: 'assigned' }, plan: { kind: 'case', run_id: 96, snapshot: snapshot(7, 'artifact-step') } };
      },
      async appendEvents(_credentials: AgentCredentials, _runId: number, events: any[]) {
        if (events.some(event => event.type === 'run:finish')) order.push('finish');
        return { accepted: events.length, ignored: 0, last_sequence: events.at(-1).sequence, status: 'running' };
      },
      async uploadArtifact(_credentials: AgentCredentials, _runId: number, artifact: any) {
        order.push('artifact');
        expect(artifact).toMatchObject({ kind: 'screenshot', filename: 'failure.png', contentType: 'image/png' });
      },
    };
    const service = new DesktopAgentService({
      store, api, createEngine: () => new FakeEngine(result, []), loadAuthState: () => ({}), claimIntervalMs: 5,
    });
    services.push(service);
    try {
      await service.register({ serverUrl: 'https://testmaster.example.test', accessToken: 'user-token', name: 'Artifact runner' });
      await waitFor(() => order.includes('finish'));
      expect(order.indexOf('artifact')).toBeGreaterThanOrEqual(0);
      expect(order.indexOf('artifact')).toBeLessThan(order.indexOf('finish'));
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it('retries a failed event batch without changing its sequence', async () => {
    const store = new MemoryStore();
    const delivered: any[][] = [];
    const attemptedSequences: number[][] = [];
    let claimed = false;
    let appendAttempts = 0;
    const api = {
      async register() { return { id: 10, agent_key: 'agent-key-10', bootstrap_token: 'agent-bootstrap-token-uvwxyz1234' }; },
      async heartbeat() {},
      async claim() {
        if (claimed) return { run: null };
        claimed = true;
        return { run: { id: 94, status: 'assigned' }, plan: { kind: 'case', run_id: 94, snapshot: snapshot(5, 'retry-step') } };
      },
      async appendEvents(_credentials: AgentCredentials, _runId: number, events: any[]) {
        appendAttempts += 1;
        attemptedSequences.push(events.map(event => event.sequence));
        if (appendAttempts === 1) throw new Error('temporary network failure');
        delivered.push(events);
        return { accepted: events.length, ignored: 0, last_sequence: events.at(-1).sequence, status: 'running' };
      },
    };
    const service = new DesktopAgentService({
      store, api, createEngine: () => new FakeEngine(passedResult(), []),
      loadAuthState: () => ({}), claimIntervalMs: 5,
    });
    services.push(service);
    await service.register({ serverUrl: 'https://testmaster.example.test', accessToken: 'user-token', name: 'Retry runner' });
    await waitFor(() => delivered.flat().some(event => event.type === 'run:finish'));
    await service.disable();

    expect(appendAttempts).toBeGreaterThan(1);
    expect(attemptedSequences[1][0]).toBe(attemptedSequences[0][0]);
    const sequences = delivered.flat().map(event => event.sequence);
    expect(sequences).toEqual(sequences.map((_event, index) => index + 1));
  });
});
