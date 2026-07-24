import { app, safeStorage } from 'electron';
import * as fs from 'fs';
import * as path from 'path';

export interface AgentCredentials {
  serverUrl: string;
  agentId: number;
  agentKey: string;
  projectId?: number | null;
  name: string;
  token: string;
  authStateId: string | null;
  enabled: boolean;
  headless: boolean;
  maxParallel: number;
  browserEngine: 'chromium' | 'firefox' | 'webkit';
  registeredAt: string;
  updatedAt: string;
}
export interface AgentCredentialStore {
  load(): AgentCredentials | null;
  save(credentials: AgentCredentials): void;
  clear(): void;
}

export interface AgentOutboxRecord {
  runId: number;
  nextSequence: number;
  events: Record<string, unknown>[];
  deferredTerminal: Record<string, unknown> | null;
  artifacts: AgentOutboxArtifact[];
  updatedAt: string;
}

export interface AgentOutboxArtifact {
  path: string;
  kind: 'screenshot' | 'trace' | 'video';
  filename: string;
  contentType: string;
}

/** Durable, non-secret Agent event queue. Credentials remain in the encrypted store. */
export interface AgentOutboxStore {
  load(agentId: number): AgentOutboxRecord[];
  save(agentId: number, record: AgentOutboxRecord): void;
  remove(agentId: number, runId: number): void;
  clear(agentId: number): void;
}

interface EncryptedAgentFile {
  version: 1;
  encrypted: string;
}

function credentialsPath(): string {
  return path.join(app.getPath('userData'), 'agent', 'credentials.json');
}

function outboxPath(agentId: number): string | null {
  try {
    return path.join(app.getPath('userData'), 'agent', `outbox-${agentId}.json`);
  } catch {
    // Unit tests can instantiate the service before Electron has started.
    return null;
  }
}

function normalizeOutboxRecord(value: unknown): AgentOutboxRecord | null {
  const item = value as Partial<AgentOutboxRecord> | null;
  if (!item || !Number.isInteger(item.runId) || Number(item.runId) < 1 || !Array.isArray(item.events)) return null;
  const events = item.events
    .filter(event => event && typeof event === 'object')
    .slice(0, 10_000)
    .map(event => ({ ...(event as Record<string, unknown>) }));
  const artifacts = Array.isArray(item.artifacts)
    ? item.artifacts.filter((artifact): artifact is AgentOutboxArtifact => {
      const value = artifact as Partial<AgentOutboxArtifact> | null;
      return Boolean(
        value && typeof value.path === 'string' && value.path.length > 0 && value.path.length <= 4_000 &&
        typeof value.filename === 'string' && value.filename.length > 0 && value.filename.length <= 500 &&
        typeof value.contentType === 'string' && ['screenshot', 'trace', 'video'].includes(String(value.kind)),
      );
    }).slice(0, 200).map(artifact => ({ ...artifact }))
    : [];
  return {
    runId: Number(item.runId),
    nextSequence: Number.isInteger(item.nextSequence) && Number(item.nextSequence) > 0 ? Number(item.nextSequence) : 1,
    events,
    deferredTerminal: item.deferredTerminal && typeof item.deferredTerminal === 'object'
      ? { ...(item.deferredTerminal as Record<string, unknown>) }
      : null,
    artifacts,
    updatedAt: typeof item.updatedAt === 'string' ? item.updatedAt : new Date().toISOString(),
  };
}

export class FileAgentOutboxStore implements AgentOutboxStore {
  load(agentId: number): AgentOutboxRecord[] {
    const file = outboxPath(agentId);
    if (!file || !fs.existsSync(file)) return [];
    try {
      const parsed = JSON.parse(fs.readFileSync(file, 'utf8')) as { version?: number; records?: unknown[] };
      if (parsed.version !== 1 || !Array.isArray(parsed.records)) return [];
      return parsed.records.map(normalizeOutboxRecord).filter((record): record is AgentOutboxRecord => record !== null);
    } catch {
      // Preserve a malformed file for support rather than deleting recoverable evidence.
      return [];
    }
  }

  save(agentId: number, record: AgentOutboxRecord): void {
    const records = this.load(agentId).filter(item => item.runId !== record.runId);
    records.push(normalizeOutboxRecord(record)!);
    this.write(agentId, records);
  }

  remove(agentId: number, runId: number): void {
    this.write(agentId, this.load(agentId).filter(item => item.runId !== runId));
  }

  clear(agentId: number): void {
    const file = outboxPath(agentId);
    if (file && fs.existsSync(file)) fs.unlinkSync(file);
  }

  private write(agentId: number, records: AgentOutboxRecord[]): void {
    const file = outboxPath(agentId);
    if (!file) return;
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const temporary = `${file}.${process.pid}.tmp`;
    fs.writeFileSync(temporary, JSON.stringify({ version: 1, records }), { encoding: 'utf8', mode: 0o600 });
    fs.renameSync(temporary, file);
  }
}

function requireEncryption(): void {
  if (!safeStorage.isEncryptionAvailable()) {
    throw new Error('SYSTEM_ENCRYPTION_UNAVAILABLE');
  }
}

export class SecureAgentCredentialStore implements AgentCredentialStore {
  load(): AgentCredentials | null {
    const file = credentialsPath();
    if (!fs.existsSync(file)) return null;
    requireEncryption();
    const wrapper = JSON.parse(fs.readFileSync(file, 'utf8')) as EncryptedAgentFile;
    if (wrapper.version !== 1 || typeof wrapper.encrypted !== 'string') {
      throw new Error('AGENT_CREDENTIALS_INVALID');
    }
    const plaintext = safeStorage.decryptString(Buffer.from(wrapper.encrypted, 'base64'));
    return validateCredentials(JSON.parse(plaintext));
  }

  save(credentials: AgentCredentials): void {
    requireEncryption();
    const validated = validateCredentials(credentials);
    const file = credentialsPath();
    const encrypted = safeStorage.encryptString(JSON.stringify(validated)).toString('base64');
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const temporary = `${file}.${process.pid}.tmp`;
    fs.writeFileSync(temporary, JSON.stringify({ version: 1, encrypted }), { encoding: 'utf8', mode: 0o600 });
    fs.renameSync(temporary, file);
  }

  clear(): void {
    const file = credentialsPath();
    if (fs.existsSync(file)) fs.unlinkSync(file);
  }
}

function validateCredentials(value: unknown): AgentCredentials {
  const item = value as Partial<AgentCredentials> | null;
  if (
    !item ||
    typeof item.serverUrl !== 'string' ||
    !/^https?:\/\//i.test(item.serverUrl) ||
    !Number.isInteger(item.agentId) ||
    Number(item.agentId) < 1 ||
    typeof item.agentKey !== 'string' ||
    typeof item.name !== 'string' ||
    typeof item.token !== 'string' ||
    item.token.length < 16
  ) {
    throw new Error('AGENT_CREDENTIALS_INVALID');
  }
  const maxParallel = Number.isInteger(item.maxParallel) && Number(item.maxParallel) > 0
    ? Math.min(16, Number(item.maxParallel))
    : 1;
  const engine = item.browserEngine;
  const browserEngine = engine === 'firefox' || engine === 'webkit' ? engine : 'chromium';
  return {
    serverUrl: item.serverUrl.replace(/\/+$/, ''),
    agentId: Number(item.agentId),
    agentKey: item.agentKey,
    projectId: Number.isInteger(item.projectId) && Number(item.projectId) > 0 ? Number(item.projectId) : null,
    name: item.name,
    token: item.token,
    authStateId: typeof item.authStateId === 'string' ? item.authStateId : null,
    enabled: item.enabled === true,
    headless: item.headless !== false,
    maxParallel,
    browserEngine,
    registeredAt: String(item.registeredAt || new Date().toISOString()),
    updatedAt: String(item.updatedAt || new Date().toISOString()),
  };
}
