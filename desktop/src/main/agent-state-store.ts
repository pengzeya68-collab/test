import { app, safeStorage } from 'electron';
import * as fs from 'fs';
import * as path from 'path';

export interface AgentCredentials {
  serverUrl: string;
  agentId: number;
  agentKey: string;
  name: string;
  token: string;
  authStateId: string | null;
  enabled: boolean;
  headless: boolean;
  registeredAt: string;
  updatedAt: string;
}
export interface AgentCredentialStore {
  load(): AgentCredentials | null;
  save(credentials: AgentCredentials): void;
  clear(): void;
}

interface EncryptedAgentFile {
  version: 1;
  encrypted: string;
}

function credentialsPath(): string {
  return path.join(app.getPath('userData'), 'agent', 'credentials.json');
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
  return {
    serverUrl: item.serverUrl.replace(/\/+$/, ''),
    agentId: Number(item.agentId),
    agentKey: item.agentKey,
    name: item.name,
    token: item.token,
    authStateId: typeof item.authStateId === 'string' ? item.authStateId : null,
    enabled: item.enabled === true,
    headless: item.headless !== false,
    registeredAt: String(item.registeredAt || new Date().toISOString()),
    updatedAt: String(item.updatedAt || new Date().toISOString()),
  };
}
