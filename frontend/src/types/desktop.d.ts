/**
 * Type declaration for the TestMaster Desktop API.
 *
 * When running in Electron, `window.testmaster` is exposed by the preload
 * bridge (desktop/src/preload/index.ts). When running in a regular browser,
 * `window.testmaster` is undefined and desktop features are disabled.
 */

interface DesktopVersions {
  electron: string
  node: string
  chromium: string
  platform: string
}

interface DesktopApi {
  browser: {
    launch: (opts?: {
      headless?: boolean
      slowMo?: number
      viewport?: { width: number; height: number } | null
      locale?: string | null
      timezoneId?: string | null
      colorScheme?: 'light' | 'dark' | 'no-preference' | null
    }) => Promise<{ browserVersion: string; chromiumPath: string }>
    close: () => Promise<void>
    status: () => Promise<{
      isReady: boolean
      browserVersion: string | null
      engineVersion: string
    }>
  }
  page: {
    goto: (
      url: string,
      opts?: { timeoutMs?: number; waitUntil?: string }
    ) => Promise<{ finalUrl: string; title: string }>
    screenshot: (opts?: {
      fullPage?: boolean
      outputDir?: string | null
    }) => Promise<{ path: string }>
  }
  element: {
    click: (
      locator: unknown,
      opts?: { timeoutMs?: number }
    ) => Promise<void>
    fill: (
      locator: unknown,
      value: string,
      opts?: { timeoutMs?: number }
    ) => Promise<void>
  }
  execution: {
    cancel: (targetCorrelationId: string) => Promise<void>
    runCase: (
      caseSnapshot: unknown,
      opts?: {
        environment?: { baseUrl: string; variables: Record<string, string> } | null
        headless?: boolean
        screenshotsOnFailure?: boolean
        traceOnFailure?: boolean
        debugMode?: boolean
        authStateId?: string | null
        runtimeConfigRequest?: { serverUrl: string; token: string; environmentId?: number | null } | null
        onEvent?: (event: unknown) => void
      }
    ) => { correlationId: string; promise: Promise<unknown> }
  }
  authStates: {
    list: () => Promise<Array<{ id: string; name: string; createdAt: string; updatedAt: string }>>
    saveCurrent: (name: string, id?: string) => Promise<{ id: string; name: string }>
    delete: (id: string) => Promise<void>
  }
  recorder: any
  files: any
  versions: DesktopVersions
}

interface Window {
  testmaster?: DesktopApi
}

export {}





