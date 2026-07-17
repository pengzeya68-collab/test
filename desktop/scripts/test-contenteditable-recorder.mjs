import { chromium } from 'playwright';
const browser = await chromium.connectOverCDP('http://127.0.0.1:9333');
try {
  const page = browser.contexts()[0].pages()[0];
  await page.evaluate(() => { location.hash = '#/ui-automation/cases/2'; });
  await page.getByText('用户操作流程', { exact: true }).waitFor({ timeout: 15000 });
  const html = '<meta charset="utf-8"><div id="editor" contenteditable="true" data-testid="editor">旧内容</div><script>setTimeout(()=>{editor.focus();editor.innerText="企业富文本内容";editor.dispatchEvent(new InputEvent("input",{bubbles:true,inputType:"insertText",data:"企业富文本内容"}))},500)<\/script>';
  const events = await page.evaluate(async url => {
    const captured = [];
    await window.testmaster.recorder.start({ url, slowMo: 0 }, event => captured.push(event));
    await new Promise(resolve => setTimeout(resolve, 1400));
    await window.testmaster.recorder.stop();
    return captured;
  }, 'data:text/html,' + encodeURIComponent(html));
  const fill = events.find(event => event.type === 'action' && event.step?.type === 'fill');
  if (!fill || fill.step.input?.value !== '企业富文本内容') throw new Error('CONTENTEDITABLE_NOT_RECORDED_' + JSON.stringify(events));
  console.log(JSON.stringify({ passed: true, stepType: fill.step.type, value: fill.step.input.value, locator: fill.step.locator.strategy }));
} finally {
  await browser.close();
}

