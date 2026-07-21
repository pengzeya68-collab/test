import { expect, it } from 'vitest';
import { RecorderSession } from '../src/worker/recorder-session';

it('redacts credential-bearing URLs and diagnostic text before emitting recorder events', () => {
  const recorder = new RecorderSession(() => {});
  const internals = recorder as any;
  expect(internals.redactNetworkUrl('https://shop.example.test/orders?token=real-token&visible=yes'))
    .toBe('https://shop.example.test/orders?token={{TOKEN}}&visible=yes');
  const diagnostic = internals.redactDiagnosticText('Authorization: Bearer top-secret password=plain-text');
  expect(diagnostic).not.toContain('top-secret');
  expect(diagnostic).not.toContain('plain-text');
  expect(diagnostic).toContain('[REDACTED]');
  expect(internals.redactDiagnosticText('{"token":"json-secret","message":"kept"}')).not.toContain('json-secret');
  const sensitiveStep: any = {
    type: 'fill',
    locator: { value: 'api_token', options: {}, fallbacks: [] },
    input: { value: 'raw-api-token', secret: false },
  };
  internals.redactRecordedStep(sensitiveStep);
  expect(sensitiveStep.input.value).toBe('{{SENSITIVE_VALUE}}');
  expect(sensitiveStep.input.secret).toBe(true);
});
