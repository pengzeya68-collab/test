/**
 * IPC contract definitions 閳?Section 4.3 of the Implementation Spec.
 *
 * Every IPC call and worker message has:
 *   - A named request and response type
 *   - Runtime validation with Zod
 *   - A correlation ID
 *   - A defined error code
 *   - A timeout and cancellation behavior
 *
 * The renderer never owns:
 *   - Direct Node.js filesystem access
 *   - Playwright browser objects
 *   - Raw database credentials
 *   - Unrestricted Electron IPC
 */

import { z } from 'zod';
import { LocatorSchema } from './locator';
import { StepSnapshotSchema, RetryConfigSchema } from './steps';

// ==================================================================
// Generic envelope
// ==================================================================

/** Correlation ID 閳?unique per request, used to match responses. */
export const CorrelationIdSchema = z.string().uuid();

/** Standard error codes for IPC responses. */
export const IPC_ERROR_CODES = [
  'OK',
  'TIMEOUT',
  'CANCELLED',
  'VALIDATION_ERROR',
  'NOT_FOUND',
  'PERMISSION_DENIED',
  'BROWSER_LAUNCH_FAILED',
  'BROWSER_NOT_READY',
  'EXECUTION_ERROR',
  'INTERNAL_ERROR',
] as const;

export type IpcErrorCode = (typeof IPC_ERROR_CODES)[number];

/** Generic request envelope. */
export const IpcRequestEnvelope = z.object({
  correlationId: CorrelationIdSchema,
  type: z.string(),
  payload: z.unknown(),
});

/** Generic response envelope. */
export const IpcResponseEnvelope = z.object({
  correlationId: CorrelationIdSchema,
  type: z.string(),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z.unknown().nullable().default(null),
});

export type IpcRequestEnvelope = z.infer<typeof IpcRequestEnvelope>;
export type IpcResponseEnvelope = z.infer<typeof IpcResponseEnvelope>;

/** Default IPC timeout in milliseconds. */
export const IPC_DEFAULT_TIMEOUT_MS = 30_000;

// ==================================================================
// Request / Response type pairs
// ==================================================================

// ------------------------------------------------------------------
// 1. Browser lifecycle
// ------------------------------------------------------------------

export const LaunchBrowserRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('browser.launch'),
  payload: z.object({
    headless: z.boolean().default(false),
    slowMo: z.number().int().min(0).max(5000).default(0),
    viewport: z
      .object({
        width: z.number().int().min(320).max(3840),
        height: z.number().int().min(240).max(2160),
      })
      .nullable()
      .default(null),
    locale: z.string().nullable().default(null),
    timezoneId: z.string().nullable().default(null),
    colorScheme: z.enum(['light', 'dark', 'no-preference']).nullable().default(null),
  }),
});

export const LaunchBrowserResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('browser.launch:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z
    .object({
      browserVersion: z.string(),
      chromiumPath: z.string(),
    })
    .nullable()
    .default(null),
});

export const CloseBrowserRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('browser.close'),
  payload: z.object({}).default({}),
});

export const CloseBrowserResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('browser.close:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z.null().default(null),
});

export const BrowserStatusRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('browser.status'),
  payload: z.object({}).default({}),
});

export const BrowserStatusResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('browser.status:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z
    .object({
      isReady: z.boolean(),
      browserVersion: z.string().nullable(),
      engineVersion: z.string(),
    })
    .nullable()
    .default(null),
});

// ------------------------------------------------------------------
// 2. Navigation
// ------------------------------------------------------------------

export const GotoRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('page.goto'),
  payload: z.object({
    url: z.string().url(),
    timeoutMs: z.number().int().min(1000).max(120000).default(30000),
    waitUntil: z
      .enum(['load', 'domcontentloaded', 'networkidle'])
      .default('load'),
  }),
});

export const GotoResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('page.goto:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z
    .object({
      finalUrl: z.string(),
      title: z.string(),
    })
    .nullable()
    .default(null),
});

// ------------------------------------------------------------------
// 3. Element operations
// ------------------------------------------------------------------

export const ClickRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('element.click'),
  payload: z.object({
    locator: LocatorSchema,
    timeoutMs: z.number().int().min(100).max(120000).default(10000),
  }),
});

export const ClickResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('element.click:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z.null().default(null),
});

export const FillRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('element.fill'),
  payload: z.object({
    locator: LocatorSchema,
    value: z.string(),
    timeoutMs: z.number().int().min(100).max(120000).default(10000),
  }),
});

export const FillResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('element.fill:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z.null().default(null),
});

// ------------------------------------------------------------------
// 4. Screenshot
// ------------------------------------------------------------------

export const ScreenshotRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('page.screenshot'),
  payload: z.object({
    fullPage: z.boolean().default(false),
  }),
});

export const ScreenshotResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('page.screenshot:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z
    .object({
      path: z.string(),
    })
    .nullable()
    .default(null),
});

// ------------------------------------------------------------------
// 5. Artifact file access
// ------------------------------------------------------------------
export const ReadArtifactRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('artifact.read'),
  payload: z.object({
    path: z.string().min(1),
  }),
});

export const ReadArtifactResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('artifact.read:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z.object({
    filename: z.string(),
    sizeBytes: z.number().int().nonnegative(),
    contentBase64: z.string(),
  }).nullable().default(null),
});
// ------------------------------------------------------------------
// 6. Run case (local execution)
// ------------------------------------------------------------------

export const RunCaseRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('case.run'),
  payload: z.object({
    caseSnapshot: z.object({
      case_id: z.number().int(),
      name: z.string(),
      base_url: z.string().nullable(),
      default_timeout_ms: z.number().int().default(10000),
      navigation_timeout_ms: z.number().int().default(30000),
      steps: z.array(StepSnapshotSchema),
    }),
    environment: z
      .object({
        baseUrl: z.string(),
        variables: z.record(z.string()).default({}),
      })
      .nullable()
      .default(null),
    headless: z.boolean().default(false),
    screenshotsOnFailure: z.boolean().default(true),
    traceOnFailure: z.boolean().default(true),
    debugMode: z.boolean().default(false),
    authStateId: z.string().uuid().nullable().optional(),
    runtimeConfigRequest: z.object({ serverUrl: z.string().url(), token: z.string().min(1), environmentId: z.number().int().nullable().optional() }).nullable().optional(),
    variables: z.record(z.string()).optional(),
  }),
});

export const RunCaseResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('case.run:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z
    .object({
      status: z.enum(['passed', 'failed', 'cancelled', 'error']),
      totalSteps: z.number().int(),
      passedSteps: z.number().int(),
      failedSteps: z.number().int(),
      durationMs: z.number().int(),
      tracePath: z.string().nullable().default(null),
      stepResults: z.array(
        z.object({
          stepId: z.string(),
          status: z.enum(['passed', 'failed', 'skipped', 'cancelled']),
          durationMs: z.number().int(),
          error: z.string().nullable(),
          screenshotPath: z.string().nullable(),
        })
      ),
    })
    .nullable()
    .default(null),
});

// ------------------------------------------------------------------
// 7. Cancel
// ------------------------------------------------------------------

export const CancelRequestSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('execution.cancel'),
  payload: z.object({
    targetCorrelationId: CorrelationIdSchema,
  }),
});

export const CancelResponseSchema = z.object({
  correlationId: CorrelationIdSchema,
  type: z.literal('execution.cancel:response'),
  success: z.boolean(),
  errorCode: z.enum(IPC_ERROR_CODES).default('OK'),
  errorMessage: z.string().nullable().default(null),
  data: z.null().default(null),
});

// ==================================================================
// Type registry 閳?maps request type to request/response schemas
// ==================================================================

export const IPC_SCHEMAS = {
  'browser.launch': {
    request: LaunchBrowserRequestSchema,
    response: LaunchBrowserResponseSchema,
    timeoutMs: 60_000,
  },
  'browser.close': {
    request: CloseBrowserRequestSchema,
    response: CloseBrowserResponseSchema,
    timeoutMs: 15_000,
  },
  'browser.status': {
    request: BrowserStatusRequestSchema,
    response: BrowserStatusResponseSchema,
    timeoutMs: 5_000,
  },
  'page.goto': {
    request: GotoRequestSchema,
    response: GotoResponseSchema,
    timeoutMs: 60_000,
  },
  'element.click': {
    request: ClickRequestSchema,
    response: ClickResponseSchema,
    timeoutMs: 30_000,
  },
  'element.fill': {
    request: FillRequestSchema,
    response: FillResponseSchema,
    timeoutMs: 30_000,
  },
  'page.screenshot': {
    request: ScreenshotRequestSchema,
    response: ScreenshotResponseSchema,
    timeoutMs: 15_000,
  },
  'artifact.read': {
    request: ReadArtifactRequestSchema,
    response: ReadArtifactResponseSchema,
    timeoutMs: 15_000,
  },
  'case.run': {
    request: RunCaseRequestSchema,
    response: RunCaseResponseSchema,
    timeoutMs: 600_000, // 10 minutes for a full case run
  },
  'execution.cancel': {
    request: CancelRequestSchema,
    response: CancelResponseSchema,
    timeoutMs: 10_000,
  },
} as const;

export type IpcType = keyof typeof IPC_SCHEMAS;

// ==================================================================
// Helpers
// ==================================================================

/** Generate a new correlation ID. */
export function newCorrelationId(): string {
  // Use crypto.randomUUID if available (Node 16+)
  const { randomUUID } = require('crypto');
  return randomUUID();
}

/** Validate an incoming request against the registered schema. */
export function validateRequest<T extends IpcType>(
  type: T,
  raw: unknown
): z.infer<(typeof IPC_SCHEMAS)[T]['request']> {
  const schema = IPC_SCHEMAS[type]?.request;
  if (!schema) {
    throw new Error(`Unknown IPC type: ${type}`);
  }
  return schema.parse(raw) as z.infer<(typeof IPC_SCHEMAS)[T]['request']>;
}

/** Create a standard error response. */
export function createErrorResponse(
  correlationId: string,
  type: string,
  errorCode: IpcErrorCode,
  errorMessage: string
): IpcResponseEnvelope {
  return {
    correlationId,
    type: `${type}:response`,
    success: false,
    errorCode,
    errorMessage,
    data: null,
  };
}

/** Create a standard success response. */
export function createSuccessResponse(
  correlationId: string,
  type: string,
  data: unknown
): IpcResponseEnvelope {
  return {
    correlationId,
    type: `${type}:response`,
    success: true,
    errorCode: 'OK',
    errorMessage: null,
    data,
  };
}







