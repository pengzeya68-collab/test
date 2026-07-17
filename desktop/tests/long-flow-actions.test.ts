import { expect, it } from 'vitest';
import { CaseExecutionEngine } from '../src/worker/execution-engine';

const loc = (strategy: any, value: string) => ({ strategy, value, options: {}, fallbacks: [], framePath: [] });
const step = (id: string, type: string, locator: any = null, input: any = null) => ({
  id, order: 10, name: id, type, enabled: true, breakpoint: false, locator, input,
  timeout_ms: 5000, retry: { count: 0, delay_ms: 0 }, continue_on_failure: false,
  screenshot: 'never' as const, condition: null, children: [],
});

it('executes rich editing, drag-drop, assertions and extracted variables as one flow', async () => {
  const html = [
    '<meta charset="utf-8">',
    '<div id="editor" contenteditable="true">旧内容</div>',
    '<input id="sourceInput"><input id="copyInput">',
    '<input id="check" type="checkbox">',
    '<button id="enabled">可用</button><button id="disabled" disabled>禁用</button>',
    '<div class="item">A</div><div class="item">B</div>',
    '<div id="drag" draggable="true">拖我</div><div id="drop">放这里</div>',
    '<script>drag.addEventListener("dragstart",e=>e.dataTransfer.setData("text/plain","ok"));drop.addEventListener("dragover",e=>e.preventDefault());drop.addEventListener("drop",e=>{e.preventDefault();drop.dataset.dropped=e.dataTransfer.getData("text/plain")});<\/script>',
  ].join('');
  const url = 'data:text/html,' + encodeURIComponent(html);
  const steps = [
    step('open', 'goto', null, { url }),
    step('rich', 'fill', loc('css', '#editor'), { value: '新内容' }),
    step('rich-check', 'assert_text_equals', loc('css', '#editor'), { expected: '新内容' }),
    step('type', 'type', loc('css', '#sourceInput'), { value: 'abc', delay_ms: 5 }),
    step('value-check', 'assert_value', loc('css', '#sourceInput'), { expected: 'abc' }),
    step('checked', 'check', loc('css', '#check')),
    step('checked-check', 'assert_checked', loc('css', '#check')),
    step('enabled', 'assert_enabled', loc('css', '#enabled')),
    step('disabled', 'assert_disabled', loc('css', '#disabled')),
    step('editable', 'assert_editable', loc('css', '#sourceInput')),
    step('count', 'assert_element_count', loc('css', '.item'), { expected: 2 }),
    step('css', 'assert_css_property', loc('css', '#disabled'), { name: 'display', expected: 'inline-block' }),
    step('extract', 'extract_value', loc('css', '#sourceInput'), { name: 'captured' }),
    step('copy', 'fill', loc('css', '#copyInput'), { value: '{{captured}}' }),
    step('copy-check', 'assert_value', loc('css', '#copyInput'), { expected: 'abc' }),
    step('drag', 'drag_and_drop', loc('css', '#drag'), { targetLocator: loc('css', '#drop') }),
    step('drop-check', 'assert_attribute', loc('css', '#drop'), { name: 'data-dropped', expected: 'ok' }),
    step('extract-url', 'extract_url', null, { name: 'currentUrl' }),
    step('url-check', 'assert_url', null, { expected: '{{currentUrl}}' }),
  ];
  const result = await new CaseExecutionEngine().execute({
    case_id: 994, name: 'long flow actions', base_url: null,
    default_timeout_ms: 5000, navigation_timeout_ms: 5000, steps,
  }, null, { headless: true, screenshotsOnFailure: true, traceOnFailure: false }, () => {});
  expect(result.status, JSON.stringify(result)).toBe('passed');
  expect(result.passedSteps).toBe(steps.length);
});

