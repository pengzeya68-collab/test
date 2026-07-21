const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const root = path.resolve(__dirname, '..', '..');
const runtimeDir = path.join(root, 'test-results', 'e2e-runtime');
const databasePath = path.resolve(process.env.E2E_DATABASE_PATH || path.join(runtimeDir, 'testmaster.sqlite3'));
const projectPython = process.platform === 'win32'
  ? path.join(root, '.venv', 'Scripts', 'python.exe')
  : path.join(root, '.venv', 'bin', 'python');
const python = process.env.E2E_PYTHON
  || (fs.existsSync(projectPython) ? projectPython : null)
  || process.env.PYTHON
  || 'python';
const port = String(process.env.E2E_BACKEND_PORT || '5101');
const databaseURL = `sqlite+aiosqlite:///${databasePath.replace(/\\/g, '/')}`;

fs.mkdirSync(runtimeDir, { recursive: true });
for (const suffix of ['', '-shm', '-wal']) {
  const candidate = `${databasePath}${suffix}`;
  if (fs.existsSync(candidate)) fs.unlinkSync(candidate);
}

const env = {
  ...process.env,
  ENVIRONMENT: 'development',
  DATABASE_URL: databaseURL,
  SECRET_KEY: 'testmaster-e2e-secret-key-not-for-production',
  ADMIN_SECRET_KEY: 'testmaster-e2e-admin-secret-not-for-production',
  ADMIN_PASSWORD: process.env.E2E_PASSWORD || 'admin123',
  TESTMASTER_ENCRYPTION_KEY: 'MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=',
  TESTMASTER_DESKTOP_LOCAL: '1',
  TESTMASTER_DESKTOP_ADMIN: process.env.E2E_USERNAME || 'admin',
  TESTMASTER_DESKTOP_PASSWORD: process.env.E2E_PASSWORD || 'admin123',
  AUTO_CREATE_TABLES_ON_STARTUP: 'false',
  HOST: '127.0.0.1',
  PORT: port,
  RELOAD: 'false',
  AUTO_TEST_BASE_URL: process.env.E2E_BACKEND_URL || `http://127.0.0.1:${port}`,
  CORS_ORIGINS: `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT || '5174'}`,
};

const migration = spawnSync(
  python,
  ['-m', 'alembic', '-c', 'fastapi_backend/alembic.ini', 'upgrade', 'head'],
  { cwd: root, env, stdio: 'inherit' },
);
if (migration.status !== 0) process.exit(migration.status || 1);

const backend = spawn(
  python,
  ['-m', 'uvicorn', 'fastapi_backend.main:app', '--host', '127.0.0.1', '--port', port],
  { cwd: root, env, stdio: 'inherit' },
);

const stop = (signal) => {
  if (!backend.killed) backend.kill(signal);
};
process.on('SIGINT', () => stop('SIGINT'));
process.on('SIGTERM', () => stop('SIGTERM'));
backend.on('exit', (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exit(code || 0);
});
