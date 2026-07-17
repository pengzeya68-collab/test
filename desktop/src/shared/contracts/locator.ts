/**
 * Locator model 鈥?Section 8 of the Implementation Spec.
 *
 * Supported locator strategies, in preferred order:
 *   test_id > role > label > placeholder > text > css > xpath
 */

import { z } from 'zod';

// ------------------------------------------------------------------
// Enums / constants
// ------------------------------------------------------------------

export const LOCATOR_STRATEGIES = [
  'test_id',
  'role',
  'label',
  'placeholder',
  'text',
  'css',
  'xpath',
] as const;

export type LocatorStrategy = (typeof LOCATOR_STRATEGIES)[number];

export interface Locator {
  strategy: LocatorStrategy;
  value: string;
  options: Record<string, unknown>;
  fallbacks: Locator[];
  framePath: string[];
}

// ------------------------------------------------------------------
// Zod schemas
// ------------------------------------------------------------------

export const LocatorSchema: z.ZodType<Locator> = z.object({
  strategy: z.enum(LOCATOR_STRATEGIES),
  value: z.string().min(1).max(2000),
  options: z.record(z.unknown()).default({}),
  fallbacks: z.array(z.lazy(() => LocatorSchema)).default([]),
  framePath: z.array(z.string()).default([]),
});

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

/**
 * Reject generated selectors containing volatile IDs, long nth-child chains,
 * absolute /html/body XPath, or framework-generated class hashes.
 *
 * Returns `true` if the locator is **rejected** (bad quality).
 */
export function isVolatileLocator(locator: Locator): boolean {
  const { strategy, value } = locator;

  if (strategy === 'xpath') {
    // Reject absolute XPath starting with /html/body
    if (/^\/(html\/)?body/i.test(value.trim())) return true;
    // Reject very long XPath (likely fragile)
    if (value.split('/').length > 15) return true;
  }

  if (strategy === 'css') {
    // Reject long nth-child chains
    const nthChildCount = (value.match(/nth-child/g) || []).length;
    if (nthChildCount > 3) return true;
    // Reject framework-generated class hashes (e.g. css-1a2b3c, sc-abc123)
    if (/(?:css|sc|styled|emotion|mui)-[a-z0-9]{5,}/i.test(value)) return true;
  }

  // Reject volatile ID patterns (React key, Vue v-id, random hashes)
  if (/^(?:react|vue|ember|angular)[\w-]*\d+$/.test(value)) return true;
  if (/^[a-f0-9]{16,}$/i.test(value)) return true;

  return false;
}

