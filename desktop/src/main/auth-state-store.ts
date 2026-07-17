import { app, safeStorage } from 'electron';
import * as fs from 'fs';
import * as path from 'path';
import { randomUUID } from 'crypto';

export interface AuthStateSummary {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}

interface StoredAuthState extends AuthStateSummary {
  encryptedState: string;
}

function rootDir(): string {
  return path.join(app.getPath('userData'), 'auth-states');
}

function statePath(id: string): string {
  if (!/^[a-f0-9-]{36}$/i.test(id)) throw new Error('INVALID_AUTH_STATE_ID');
  return path.join(rootDir(), id + '.json');
}

function requireEncryption(): void {
  if (!safeStorage.isEncryptionAvailable()) throw new Error('SYSTEM_ENCRYPTION_UNAVAILABLE');
}

export function listAuthStates(): AuthStateSummary[] {
  const dir = rootDir();
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(name => /^[a-f0-9-]{36}\.json$/i.test(name))
    .map(name => {
      try {
        const item = JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8')) as StoredAuthState;
        return { id: item.id, name: item.name, createdAt: item.createdAt, updatedAt: item.updatedAt };
      } catch {
        return null;
      }
    })
    .filter((item): item is AuthStateSummary => Boolean(item))
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function saveAuthState(name: string, storageState: object, id?: string): AuthStateSummary {
  requireEncryption();
  const cleanName = name.trim().slice(0, 100);
  if (!cleanName) throw new Error('AUTH_STATE_NAME_REQUIRED');
  const stateId = id || randomUUID();
  const file = statePath(stateId);
  const now = new Date().toISOString();
  const existing = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) as StoredAuthState : null;
  const encryptedState = safeStorage.encryptString(JSON.stringify(storageState)).toString('base64');
  const item: StoredAuthState = {
    id: stateId,
    name: cleanName,
    createdAt: existing?.createdAt || now,
    updatedAt: now,
    encryptedState,
  };
  fs.mkdirSync(rootDir(), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(item, null, 2), { encoding: 'utf8', mode: 0o600 });
  return { id: item.id, name: item.name, createdAt: item.createdAt, updatedAt: item.updatedAt };
}

export function loadAuthState(id: string): any {
  requireEncryption();
  const item = JSON.parse(fs.readFileSync(statePath(id), 'utf8')) as StoredAuthState;
  const decrypted = safeStorage.decryptString(Buffer.from(item.encryptedState, 'base64'));
  return JSON.parse(decrypted);
}

export function deleteAuthState(id: string): void {
  const file = statePath(id);
  if (fs.existsSync(file)) fs.unlinkSync(file);
}

