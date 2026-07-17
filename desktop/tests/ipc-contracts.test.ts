/**
 * IPC contract validation tests 鈥?Phase 0 gate.
 *
 * Verifies that every IPC schema defined in the contract:
 *   1. Accepts valid input
 *   2. Rejects invalid input
 *   3. Has a correlation ID, timeout, and error code
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';
import {
  IPC_SCHEMAS,
  IpcType,
  IPC_ERROR_CODES,
  newCorrelationId,
  validateRequest,
  createSuccessResponse,
  createErrorResponse,
  LaunchBrowserRequestSchema,
  GotoRequestSchema,
  ClickRequestSchema,
  FillRequestSchema,
  RunCaseRequestSchema,
} from '../src/shared/contracts/ipc';
import { LocatorSchema, isVolatileLocator } from '../src/shared/contracts/locator';
import {
  StepSnapshotSchema,
  STEP_TYPES,
  validateStepType,
} from '../src/shared/contracts/steps';

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

const validCorrelationId = '00000000-0000-0000-0000-000000000001';

// ------------------------------------------------------------------
// IPC contract tests
// ------------------------------------------------------------------

describe('IPC Error Codes', () => {
  it('should define all required error codes', () => {
    expect(IPC_ERROR_CODES).toContain('OK');
    expect(IPC_ERROR_CODES).toContain('TIMEOUT');
    expect(IPC_ERROR_CODES).toContain('CANCELLED');
    expect(IPC_ERROR_CODES).toContain('VALIDATION_ERROR');
    expect(IPC_ERROR_CODES).toContain('BROWSER_LAUNCH_FAILED');
    expect(IPC_ERROR_CODES).toContain('INTERNAL_ERROR');
  });
});

describe('Correlation ID', () => {
  it('should generate valid UUIDs', () => {
    const id = newCorrelationId();
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
  });

  it('should generate unique IDs', () => {
    const id1 = newCorrelationId();
    const id2 = newCorrelationId();
    expect(id1).not.toBe(id2);
  });
});

describe('Browser Launch Request Schema', () => {
  it('should accept valid request with defaults', () => {
    const req = LaunchBrowserRequestSchema.parse({
      correlationId: validCorrelationId,
      type: 'browser.launch',
      payload: {},
    });
    expect(req.payload.headless).toBe(false); // default
    expect(req.payload.slowMo).toBe(0); // default
    expect(req.payload.viewport).toBeNull(); // default
  });

  it('should accept full request', () => {
    const req = LaunchBrowserRequestSchema.parse({
      correlationId: validCorrelationId,
      type: 'browser.launch',
      payload: {
        headless: true,
        slowMo: 500,
        viewport: { width: 1920, height: 1080 },
        locale: 'zh-CN',
        timezoneId: 'Asia/Shanghai',
        colorScheme: 'dark',
      },
    });
    expect(req.payload.headless).toBe(true);
    expect(req.payload.locale).toBe('zh-CN');
  });

  it('should reject invalid correlation ID', () => {
    expect(() =>
      LaunchBrowserRequestSchema.parse({
        correlationId: 'not-a-uuid',
        type: 'browser.launch',
        payload: {},
      })
    ).toThrow();
  });

  it('should reject invalid type', () => {
    expect(() =>
      LaunchBrowserRequestSchema.parse({
        correlationId: validCorrelationId,
        type: 'wrong.type',
        payload: {},
      })
    ).toThrow();
  });
});

describe('Goto Request Schema', () => {
  it('should accept valid URL', () => {
    const req = GotoRequestSchema.parse({
      correlationId: validCorrelationId,
      type: 'page.goto',
      payload: { url: 'https://example.com' },
    });
    expect(req.payload.url).toBe('https://example.com');
    expect(req.payload.timeoutMs).toBe(30000); // default
  });

  it('should reject invalid URL', () => {
    expect(() =>
      GotoRequestSchema.parse({
        correlationId: validCorrelationId,
        type: 'page.goto',
        payload: { url: 'not-a-url' },
      })
    ).toThrow();
  });
});

describe('Click Request Schema', () => {
  it('should accept valid locator', () => {
    const req = ClickRequestSchema.parse({
      correlationId: validCorrelationId,
      type: 'element.click',
      payload: {
        locator: {
          strategy: 'role',
          value: 'button',
          options: { name: 'Submit' },
        },
      },
    });
    expect(req.payload.locator.strategy).toBe('role');
  });
});

describe('Fill Request Schema', () => {
  it('should accept valid input', () => {
    const req = FillRequestSchema.parse({
      correlationId: validCorrelationId,
      type: 'element.fill',
      payload: {
        locator: { strategy: 'css', value: '#username' },
        value: 'testuser',
      },
    });
    expect(req.payload.value).toBe('testuser');
  });
});


describe('Artifact Read Request Schema', () => {
  it('should accept a valid artifact path', () => {
    const req = validateRequest('artifact.read', {
      correlationId: validCorrelationId,
      type: 'artifact.read',
      payload: { path: 'C:/tmp/test.png' },
    })
    expect(req.payload.path).toBe('C:/tmp/test.png')
  })
})
describe('Response helpers', () => {
  it('should create success response', () => {
    const resp = createSuccessResponse(validCorrelationId, 'browser.launch', {
      browserVersion: '131.0.0',
    });
    expect(resp.success).toBe(true);
    expect(resp.errorCode).toBe('OK');
    expect(resp.data).toEqual({ browserVersion: '131.0.0' });
  });

  it('should create error response', () => {
    const resp = createErrorResponse(
      validCorrelationId,
      'browser.launch',
      'BROWSER_LAUNCH_FAILED',
      'Chromium not found'
    );
    expect(resp.success).toBe(false);
    expect(resp.errorCode).toBe('BROWSER_LAUNCH_FAILED');
    expect(resp.errorMessage).toBe('Chromium not found');
  });
});

// ------------------------------------------------------------------
// Schema completeness
// ------------------------------------------------------------------

describe('IPC Schema Registry', () => {
  it('should define all required IPC types', () => {
    const requiredTypes: IpcType[] = [
      'browser.launch',
      'browser.close',
      'browser.status',
      'page.goto',
      'element.click',
      'element.fill',
      'page.screenshot',
      'artifact.read',
      'case.run',
      'execution.cancel',
    ];
    for (const type of requiredTypes) {
      expect(IPC_SCHEMAS[type]).toBeDefined();
      expect(IPC_SCHEMAS[type].request).toBeDefined();
      expect(IPC_SCHEMAS[type].response).toBeDefined();
      expect(IPC_SCHEMAS[type].timeoutMs).toBeGreaterThan(0);
    }
  });
});

// ------------------------------------------------------------------
// Locator tests
// ------------------------------------------------------------------

describe('Locator Schema', () => {
  it('should accept all supported strategies', () => {
    const strategies = ['test_id', 'role', 'label', 'placeholder', 'text', 'css', 'xpath'];
    for (const strategy of strategies) {
      const loc = LocatorSchema.parse({
        strategy,
        value: 'test-value',
      });
      expect(loc.strategy).toBe(strategy);
    }
  });

  it('should reject empty value', () => {
    expect(() =>
      LocatorSchema.parse({ strategy: 'css', value: '' })
    ).toThrow();
  });

  it('should detect volatile XPath', () => {
    expect(
      isVolatileLocator({
        strategy: 'xpath',
        value: '/html/body/div/div[1]/div[2]/button',
      })
    ).toBe(true);
  });

  it('should detect volatile CSS nth-child chains', () => {
    expect(
      isVolatileLocator({
        strategy: 'css',
        value: 'div:nth-child(1) > span:nth-child(2) > a:nth-child(3) > button:nth-child(4)',
      })
    ).toBe(true);
  });

  it('should not reject good CSS selectors', () => {
    expect(
      isVolatileLocator({
        strategy: 'css',
        value: '#login-button',
      })
    ).toBe(false);
  });
});

// ------------------------------------------------------------------
// Step type tests
// ------------------------------------------------------------------

describe('Step Types', () => {
  it('should include all Phase 1 required step types', () => {
    const required = ['goto', 'click', 'fill', 'assert_visible', 'assert_text_equals'];
    for (const type of required) {
      expect(STEP_TYPES).toContain(type);
    }
  });

  it('should validate known step type', () => {
    expect(() => validateStepType('goto')).not.toThrow();
    expect(() => validateStepType('click')).not.toThrow();
  });

  it('should reject unknown step type', () => {
    expect(() => validateStepType('unknown_action')).toThrow();
  });
});

describe('Step Snapshot Schema', () => {
  it('should accept a valid step', () => {
    const step = StepSnapshotSchema.parse({
      id: 'step-001',
      order: 10,
      type: 'goto',
      locator: null,
      input: { url: 'https://example.com' },
    });
    expect(step.id).toBe('step-001');
    expect(step.enabled).toBe(true); // default
    expect(step.breakpoint).toBe(false); // default
  });

  it('should require id and type', () => {
    expect(() => StepSnapshotSchema.parse({ order: 10 })).toThrow();
  });
});

