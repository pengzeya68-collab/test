const fs = require('fs');
const path = require('path');

const bundledChromium = path.join(
  __dirname,
  'playwright-browsers',
  'chromium-1148',
  'chrome-win',
  'chrome.exe',
);

const executablePath = process.env.PLAYWRIGHT_CHROMIUM_PATH
  || (fs.existsSync(bundledChromium) ? bundledChromium : undefined);
const frontendPort = Number(process.env.E2E_FRONTEND_PORT || 5174);
const backendPort = Number(process.env.E2E_BACKEND_PORT || 5101);
const frontendURL = process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${frontendPort}`;
const backendURL = process.env.E2E_BACKEND_URL || `http://127.0.0.1:${backendPort}`;
const useExistingServers = process.env.E2E_USE_EXISTING_SERVERS === 'true';

const webServer = useExistingServers ? undefined : [
  {
    command: 'node e2e/scripts/start-backend.js',
    url: `${backendURL}/api/health`,
    reuseExistingServer: false,
    timeout: 120000,
    env: {
      E2E_BACKEND_PORT: String(backendPort),
      E2E_BACKEND_URL: backendURL,
    },
  },
  {
    command: `npm --prefix frontend run dev -- --host 127.0.0.1 --port ${frontendPort} --strictPort`,
    url: frontendURL,
    reuseExistingServer: false,
    timeout: 120000,
    env: {
      VITE_FASTAPI_BASE_URL: backendURL,
      VITE_SERVER_URL: backendURL,
    },
  },
];

module.exports = {
  testDir: './e2e',
  timeout: 60000,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: frontendURL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer,
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        launchOptions: executablePath ? { executablePath } : undefined,
      },
    },
  ],
};
