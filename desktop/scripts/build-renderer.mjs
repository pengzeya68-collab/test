import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(scriptDir, '..', '..', 'frontend');
const npmCli = path.resolve(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js');
const child = spawn(process.execPath, [npmCli, 'run', 'build'], {
  cwd: frontendDir,
  env: {
    ...process.env,
    VITE_DESKTOP_BUILD: 'true',
    VITE_API_BASE_URL: 'http://127.0.0.1:5001/api/v1',
    VITE_AUTO_TEST_BASE_URL: 'http://127.0.0.1:5001/api',
  },
  stdio: 'inherit',
});
child.on('exit', (code) => process.exit(code ?? 1));
child.on('error', (error) => { console.error(error); process.exit(1); });