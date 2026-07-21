import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const desktopDir = path.resolve(scriptDir, '..');
const frontendDir = path.resolve(desktopDir, '..', 'frontend');
// 桌面 renderer 直接输出到 desktop/dist/renderer，不再借道 frontend/dist。
// 之前的做法（先构建进 frontend/dist 再拷贝）会让桌面产物污染 Web 构建目录，
// 导致 frontend/dist 残留孤立的桌面 chunk，且"最后一次构建决定目录内容"，极易部署错版本。
const rendererOutDir = path.resolve(desktopDir, 'dist', 'renderer');
const npmCli = path.resolve(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js');
const child = spawn(process.execPath, [npmCli, 'run', 'build', '--', '--mode', 'desktop', '--outDir', rendererOutDir, '--emptyOutDir'], {
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
