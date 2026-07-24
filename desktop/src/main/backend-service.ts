import { app } from 'electron';
import { ChildProcess, spawn } from 'child_process';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

const DEFAULT_BACKEND_PORT = 5001;
let backendProcess: ChildProcess | null = null;

interface DesktopJMeterRuntime {
  JMETER_ENGINE_ENABLED: 'true' | 'false';
  JMETER_HOME?: string;
  JMETER_BIN?: string;
  JMETER_REPORT_DIR: string;
}

/**
 * Keep normal installations on the conventional loopback port while allowing
 * isolated support and acceptance launches to avoid attaching to an older
 * desktop process that is still listening on 5001.
 */
export function resolveLocalBackendPort(environment: NodeJS.ProcessEnv = process.env): number {
  const raw = environment.TESTMASTER_DESKTOP_BACKEND_PORT || environment.TESTMASTER_BACKEND_PORT;
  if (!raw) return DEFAULT_BACKEND_PORT;
  const port = Number(raw);
  return Number.isInteger(port) && port >= 1024 && port <= 65535
    ? port
    : DEFAULT_BACKEND_PORT;
}

function localHealthUrl(environment: NodeJS.ProcessEnv = process.env): string {
  return `http://127.0.0.1:${resolveLocalBackendPort(environment)}/api/ui-automation/health`;
}

function jmeterExecutableName(platform = process.platform): string {
  return platform === 'win32' ? 'jmeter.bat' : 'jmeter';
}

/**
 * Resolve a locally installed JMeter without making the desktop product depend
 * on a machine-specific path. Explicit environment settings always win; the
 * common Windows installation root is only a convenience fallback.
 */
export function resolveDesktopJMeterRuntime(
  dataDir: string,
  environment: NodeJS.ProcessEnv = process.env,
  platform = process.platform,
): DesktopJMeterRuntime {
  const executableName = jmeterExecutableName(platform);
  const reportDir = environment.JMETER_REPORT_DIR || path.join(dataDir, 'jmeter-reports');
  const explicitlyDisabled = String(environment.JMETER_ENGINE_ENABLED || '').toLowerCase() === 'false';
  const explicitBin = environment.JMETER_BIN;
  const explicitHome = environment.JMETER_HOME;
  const candidates = [
    explicitBin,
    explicitHome ? path.join(explicitHome, 'bin', executableName) : undefined,
    platform === 'win32' ? 'D:\\Jmeter\\apache-jmeter-5.6.3\\bin\\jmeter.bat' : undefined,
    platform === 'win32' ? 'D:\\Jmeter\\apache-jmeter-5.1.1\\bin\\jmeter.bat' : undefined,
  ].filter((value): value is string => Boolean(value));
  const bin = candidates.find(candidate => fs.existsSync(candidate));

  if (!bin || explicitlyDisabled) {
    return { JMETER_ENGINE_ENABLED: 'false', JMETER_REPORT_DIR: reportDir };
  }
  return {
    JMETER_ENGINE_ENABLED: 'true',
    JMETER_HOME: path.dirname(path.dirname(bin)),
    JMETER_BIN: bin,
    JMETER_REPORT_DIR: reportDir,
  };
}

export function persistentDesktopPassword(dataDir: string): string {
  const passwordPath = path.join(dataDir, '.desktop-admin-password');
  try {
    const current = fs.readFileSync(passwordPath, 'utf8').trim();
    if (current.length >= 16) return current;
  } catch {
    // first launch
  }
  const password = crypto.randomBytes(18).toString('base64url');
  fs.writeFileSync(passwordPath, password, { encoding: 'utf8', mode: 0o600 });
  return password;
}

/**
 * Returns the credentials created for the bundled loopback service.  This is
 * deliberately a local-file capability: it is never exposed by FastAPI or
 * persisted in renderer storage.  The IPC handler additionally limits access
 * to the application's own main window.
 */
export function readLocalBackendCredentials(dataDir: string): { username: string; password: string } | null {
  const passwordPath = path.join(dataDir, '.desktop-admin-password');
  try {
    const password = fs.readFileSync(passwordPath, 'utf8').trim();
    if (password.length < 16) return null;
    return { username: 'admin', password };
  } catch {
    return null;
  }
}

export function getLocalBackendCredentials(): { username: string; password: string } | null {
  return readLocalBackendCredentials(path.join(app.getPath('userData'), 'service'));
}

async function isHealthy(): Promise<boolean> {
  try {
    const response = await fetch(localHealthUrl(), { signal: AbortSignal.timeout(1500) });
    if (!response.ok) return false;
    const body = await response.json() as { status?: string; enabled?: boolean };
    return body.status === 'ok' && body.enabled === true;
  } catch {
    return false;
  }
}

function persistentSecret(dataDir: string, filename = '.service-secret'): string {
  const secretPath = path.join(dataDir, filename);
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
  // Use the same entry point in development and packaged builds.  Starting
  // Uvicorn directly bypassed the desktop database migration performed by the
  // frozen executable, which could leave a fresh development profile blank.
  const args = isFrozen ? [] : [path.join(projectRoot, 'desktop-backend-entry.py')];
  const stdout = fs.openSync(path.join(logDir, 'backend.log'), 'a');
  const stderr = fs.openSync(path.join(logDir, 'backend-error.log'), 'a');
  const desktopPassword = persistentDesktopPassword(dataDir);
  const jmeterRuntime = resolveDesktopJMeterRuntime(dataDir);
  backendProcess = spawn(executable, args, {
    cwd: isFrozen ? dataDir : projectRoot,
    windowsHide: true,
    stdio: ['ignore', stdout, stderr],
    env: {
      ...process.env,
      DATABASE_URL: `sqlite:///${databasePath}`,
      TESTMASTER_BACKEND_PORT: String(resolveLocalBackendPort()),
      SECRET_KEY: persistentSecret(dataDir, '.service-secret'),
      ADMIN_SECRET_KEY: persistentSecret(dataDir, '.admin-secret'),
      ADMIN_PASSWORD: desktopPassword,
      TESTMASTER_DESKTOP_LOCAL: '1',
      TESTMASTER_DESKTOP_ADMIN: 'admin',
      TESTMASTER_DESKTOP_PASSWORD: desktopPassword,
      TESTMASTER_DATA_DIR: dataDir,
      ...jmeterRuntime,
      // The frozen backend runs its bundled Alembic migrations before Uvicorn
      // starts. Never use create_all() for an existing desktop database.
      AUTO_CREATE_TABLES_ON_STARTUP: 'false',
      CORS_ORIGINS: 'null,http://127.0.0.1:5173,http://localhost:5173',
    },
  });
  backendProcess.once('error', (error) => {
    console.error('[Backend] spawn failed:', error);
    backendProcess = null;
    try { fs.closeSync(stdout); } catch {}
    try { fs.closeSync(stderr); } catch {}
  });
  backendProcess.once('exit', () => {
    backendProcess = null;
    try { fs.closeSync(stdout); } catch {}
    try { fs.closeSync(stderr); } catch {}
  });

  // A frozen backend can spend longer on its first launch extracting runtime
  // files and creating an isolated SQLite schema.  Do not report a false
  // connection failure while that legitimate cold-start work is still active.
  const deadline = Date.now() + 90000;
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
