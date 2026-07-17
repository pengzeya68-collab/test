/**
 * Step type definitions 鈥?Section 7 of the Implementation Spec.
 *
 * Every supported step type has a documented input schema.
 * Step IDs must remain stable when reordered.
 */

import { z } from 'zod';
import { LocatorSchema } from './locator';

// ------------------------------------------------------------------
// Step types
// ------------------------------------------------------------------

export const STEP_TYPES = [
  // Navigation and browser
  'goto',
  'reload',
  'go_back',
  'switch_page',
  'close_page',
  'set_viewport',
  // Element operations
  'click',
  'double_click',
  'fill',
  'type',
  'clear',
  'press',
  'check',
  'uncheck',
  'select_option',
  'hover',
  'focus',
  'scroll_into_view',
  'drag_and_drop',
  'upload_file',
  'download',
  // Context
  'accept_dialog',
  'dismiss_dialog',
  // Waits
  'wait_for_element',
  'wait_for_url',
  'wait_for_load_state',
  'wait_for_timeout',
  // Assertions
  'assert_visible',
  'assert_hidden',
  'assert_enabled',
  'assert_disabled',
  'assert_editable',
  'assert_checked',
  'assert_text_equals',
  'assert_text_contains',
  'assert_text_matches',
  'assert_value',
  'assert_attribute',
  'assert_css_property',
  'assert_element_count',
  'assert_url',
  'assert_title',
  // Variables and control flow
  'set_variable',
  'extract_text',
  'extract_value',
  'extract_attribute',
  'extract_url',
  // Group
] as const;

export type StepType = (typeof STEP_TYPES)[number];

// ------------------------------------------------------------------
// Screenshot mode
// ------------------------------------------------------------------

export const SCREENSHOT_MODES = ['always', 'on-failure', 'never'] as const;
export type ScreenshotMode = (typeof SCREENSHOT_MODES)[number];

// ------------------------------------------------------------------
// Zod schemas
// ------------------------------------------------------------------

export const RetryConfigSchema = z.object({
  count: z.number().int().min(0).max(10).default(0),
  delay_ms: z.number().int().min(0).max(60000).default(0),
});

export const StepSnapshotSchema = z.object({
  id: z.string().min(1),
  order: z.number().int().min(0),
  name: z.string().max(200).nullable().default(null),
  type: z.enum(STEP_TYPES),
  enabled: z.boolean().default(true),
  breakpoint: z.boolean().default(false),
  locator: LocatorSchema.nullable().default(null),
  input: z.any().nullable().default(null),
  timeout_ms: z.number().int().min(100).max(120000).nullable().default(null),
  retry: RetryConfigSchema.default({ count: 0, delay_ms: 0 }),
  continue_on_failure: z.boolean().default(false),
  screenshot: z.enum(SCREENSHOT_MODES).default('on-failure'),
  condition: z.string().nullable().default(null),
  children: z.array(z.lazy((): z.ZodTypeAny => StepSnapshotSchema)).default([]),
});

export type StepSnapshot = z.infer<typeof StepSnapshotSchema>;

// ------------------------------------------------------------------
// Validation helper
// ------------------------------------------------------------------

/**
 * Validate that a step type is known.
 * Throws a ZodError-style message for unknown types.
 */
export function validateStepType(type: string): asserts type is StepType {
  if (!STEP_TYPES.includes(type as StepType)) {
    throw new Error(`Unknown step type: ${type}`);
  }
}

