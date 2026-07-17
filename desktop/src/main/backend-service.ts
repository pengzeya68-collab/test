import { app } from 'electron';
import { ChildProcess, spawn } from 'child_process';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

const HEALTH_URL = 'http://127.0.0.1:5001/api/ui-automation/health';
let backendProcess: ChildProcess | null = null;

async function isHealthy(): Promise<boolean> {
  try {
    const response = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(1500) });
    if (!response.ok) return false;
    const body = await response.json() as { status?: string; enabled?: boolean };
    return body.status === 'ok' && body.enabled === true;
  } catch {
    return false;
  }
}

function persistentSecret(dataDir: string): string {
  const secretPath = path.join(dataDir, '.service-secret');
  try {
    const current = fs.readFileSync(secretPath, 'utf8').trim();
    if (current.length >= 32) return current;
  } catch {}
  const secret = crypto.randomBytes(48).toString('base64url');
  fs.writeFileSync(secretPath, secret, { encoding: 'utf8', mode: 0o600 });
  return secret;
}

function backendExecutable(): string | null {
  if (app.isPackaged) {
    const executable = path.join(process.resourcesPath, 'backend', 'testmaster-backend.exe');
    return fs.existsSync(executable) ? executable : null;
  }
  const projectRoot = path.resolve(__dirname, '../../..');
  const python = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');
  return fs.existsSync(python) ? python : null;
}

export async function ensureLocalBackend(): Promise<{ ready: boolean; managed: boolean; error?: string }> {
  if (await isHealthy()) return { ready: true, managed: false };
  const executable = backendExecutable();
  if (!executable) return { ready: false, managed: false, error: 'LOCAL_BACKEND_MISSING' };

  const dataDir = path.join(app.getPath('userData'), 'service');
  const logDir = path.join(dataDir, 'logs');
  fs.mkdirSync(logDir, { recursive: true });
  const databasePath = path.join(dataDir, 'testmaster.db').replace(/\\/g, '/');
  const isFrozen = app.isPackaged;
  const projectRoot = path.resolve(__dirname, '../../..');
  const args = isFrozen ? [] : ['-m', 'uvicorn', 'fastapi_backend.main:app', '--host', '127.0.0.1', '--port', '5001'];
  const stdout = fs.openSync(path.join(logDir, 'backend.log'), 'a');
  const stderr = fs.openSync(path.join(logDir, 'backend-error.log'), 'a');
  backendProcess = spawn(executable, args, {
    cwd: isFrozen ? dataDir : projectRoot,
    windowsHide: true,
    stdio: ['ignore', stdout, stderr],
    env: {
      ...process.env,
      DATABASE_URL: `sqlite:///${databasePath}`,
      SECRET_KEY: persistentSecret(dataDir),
      ADMIN_SECRET_KEY: persistentSecret(dataDir),
      ADMIN_PASSWORD: 'admin123',
      TESTMASTER_DESKTOP_LOCAL: '1',
      TESTMASTER_DESKTOP_ADMIN: 'admin',
      TESTMASTER_DESKTOP_PASSWORD: 'admin123',
      TESTMASTER_DATA_DIR: dataDir,
      AUTO_CREATE_TABLES_ON_STARTUP: 'true',
      CORS_ORIGINS: 'null,http://127.0.0.1:5173,http://localhost:5173',
    },
  });
  backendProcess.once('exit', () => { backendProcess = null; });

  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    if (await isHealthy()) return { ready: true, managed: true };
    if (!backendProcess) break;
    await new Promise(resolve => setTimeout(resolve, 400));
  }
  return { ready: false, managed: true, error: 'LOCAL_BACKEND_START_FAILED' };
}

export function stopLocalBackend(): void {
  if (backendProcess && !backendProcess.killed) backendProcess.kill();
  backendProcess = null;
}
