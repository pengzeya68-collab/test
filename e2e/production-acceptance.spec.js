const { test, expect } = require('@playwright/test');

const productionBaseUrl = (process.env.PRODUCTION_BASE_URL || '').replace(/\/$/, '');

test.describe('公网生产闭环验收', () => {
  test.skip(!productionBaseUrl, '仅在显式设置 PRODUCTION_BASE_URL 时运行，避免本地测试误写生产数据');

  test('注册、网页登录、项目隔离、接口用例与场景执行闭环', async ({ page, request }) => {
    const stamp = `${Date.now()}${Math.floor(Math.random() * 10000)}`;
    const username = `prodqa${stamp}`.slice(0, 20);
    const password = `Qa${stamp}x9`;
    const email = `${username}@example.test`;
    let token = '';
    let projectId = null;
    let groupId = null;
    let caseId = null;
    let scenarioId = null;

    const authHeaders = () => ({ Authorization: `Bearer ${token}` });
    const api = (path) => `${productionBaseUrl}${path}`;
    const expectOk = async (response, label) => {
      if (!response.ok()) throw new Error(`${label} failed: ${response.status()} ${await response.text()}`);
      return response.json();
    };
    const expectDeleted = async (response, label) => {
      if (!response.ok()) throw new Error(`${label} failed: ${response.status()} ${await response.text()}`);
    };

    try {
      const health = await request.get(api('/api/health'));
      expect(health.ok(), await health.text()).toBeTruthy();

      const registration = await request.post(api('/api/v1/auth/register'), {
        data: { username, email, password },
      });
      const registrationBody = await expectOk(registration, 'register');
      token = registrationBody.access_token;
      expect(token).toBeTruthy();

      const login = await request.post(api('/api/v1/auth/login'), { data: { username, password } });
      const loginBody = await expectOk(login, 'login');
      token = loginBody.access_token;
      const me = await request.get(api('/api/v1/auth/me'), { headers: authHeaders() });
      expect((await expectOk(me, 'get current user')).username).toBe(username);

      // Verify the public browser flow with the same newly registered user.
      await page.goto(`${productionBaseUrl}/#/login`, { waitUntil: 'domcontentloaded' });
      await page.getByTestId('login-username-input').fill(username);
      await page.getByTestId('login-password-input').fill(password);
      await page.getByTestId('login-submit-button').click();
      await expect(page).toHaveURL(/#\/(?:home|$)/, { timeout: 20_000 });

      const projects = await request.post(api('/api/workspace/projects'), {
        headers: authHeaders(),
        data: { name: `公网验收项目-${stamp}`, description: 'isolated production acceptance fixture' },
      });
      const project = await expectOk(projects, 'create project');
      projectId = project.id;
      expect(Number(projectId)).toBeGreaterThan(0);
      const projectHeaders = { ...authHeaders(), 'X-Project-Id': String(projectId) };

      const createdGroup = await request.post(api('/api/auto-test/groups'), {
        headers: projectHeaders,
        data: {
          name: `公网验收分组-${stamp}`,
          description: 'Fixture group required by the API case workflow',
          sort_order: 0,
        },
      });
      const groupBody = await expectOk(createdGroup, 'create api group');
      groupId = groupBody.id;
      expect(Number(groupId)).toBeGreaterThan(0);

      const createdCase = await request.post(api('/api/auto-test/cases'), {
        headers: projectHeaders,
        data: {
          group_id: groupId,
          name: `公网自检健康接口-${stamp}`,
          method: 'GET',
          url: `${productionBaseUrl}/api/health`,
          body_type: 'none',
          assertions: [{ target: 'status_code', operator: 'equals', expected: 200 }],
          description: 'Created by isolated production acceptance',
        },
      });
      const caseBody = await expectOk(createdCase, 'create api case');
      caseId = caseBody.id;

      const quickRun = await request.post(api(`/api/auto-test/cases/${caseId}/quick-run`), {
        headers: projectHeaders,
        data: {},
      });
      const quickRunBody = await expectOk(quickRun, 'run api case');
      expect(quickRunBody.success ?? quickRunBody.status === 'passed').toBeTruthy();

      const createdScenario = await request.post(api('/api/auto-test/scenarios'), {
        headers: projectHeaders,
        data: { name: `公网验收场景-${stamp}`, description: 'case-to-scenario real API chain', is_active: true },
      });
      const scenarioBody = await expectOk(createdScenario, 'create scenario');
      scenarioId = scenarioBody.id;

      const createdStep = await request.post(api(`/api/auto-test/scenarios/${scenarioId}/steps`), {
        headers: projectHeaders,
        data: { api_case_id: caseId, step_order: 1, is_active: true, step_type: 'api_request' },
      });
      await expectOk(createdStep, 'create scenario step');

      const debugRun = await request.post(api(`/api/auto-test/scenarios/${scenarioId}/debug`), {
        headers: projectHeaders,
        data: {},
      });
      const debugBody = await expectOk(debugRun, 'debug scenario');
      expect(debugBody.success ?? debugBody.status === 'passed').toBeTruthy();

      const visibleCases = await request.get(api('/api/auto-test/cases?page_size=100'), { headers: projectHeaders });
      const caseList = await expectOk(visibleCases, 'list scoped cases');
      const cases = Array.isArray(caseList) ? caseList : (caseList.items || caseList.cases || []);
      expect(cases.some(item => item.id === caseId)).toBeTruthy();

      // A production fixture is only acceptable when its full deletion path
      // succeeds and the project is no longer discoverable afterwards.
      await expectDeleted(
        await request.delete(api(`/api/auto-test/scenarios/${scenarioId}`), { headers: projectHeaders }),
        'delete scenario fixture',
      );
      scenarioId = null;
      await expectDeleted(
        await request.delete(api(`/api/auto-test/cases/${caseId}`), { headers: projectHeaders }),
        'delete api case fixture',
      );
      caseId = null;
      await expectDeleted(
        await request.delete(api(`/api/auto-test/groups/${groupId}`), { headers: projectHeaders }),
        'delete api group fixture',
      );
      groupId = null;
      await expectDeleted(
        await request.delete(api(`/api/workspace/projects/${projectId}`), { headers: authHeaders() }),
        'delete workspace fixture',
      );
      const removedProjectId = projectId;
      projectId = null;
      const remainingProjects = await expectOk(
        await request.get(api('/api/workspace/projects'), { headers: authHeaders() }),
        'list projects after cleanup',
      );
      const projectItems = Array.isArray(remainingProjects)
        ? remainingProjects
        : (remainingProjects.items || remainingProjects.projects || []);
      expect(projectItems.some(item => item.id === removedProjectId)).toBeFalsy();
    } finally {
      const cleanupHeaders = token && projectId ? { ...authHeaders(), 'X-Project-Id': String(projectId) } : null;
      if (cleanupHeaders && scenarioId) await request.delete(api(`/api/auto-test/scenarios/${scenarioId}`), { headers: cleanupHeaders }).catch(() => {});
      if (cleanupHeaders && caseId) await request.delete(api(`/api/auto-test/cases/${caseId}`), { headers: cleanupHeaders }).catch(() => {});
      if (cleanupHeaders && groupId) await request.delete(api(`/api/auto-test/groups/${groupId}`), { headers: cleanupHeaders }).catch(() => {});
      if (token && projectId) await request.delete(api(`/api/workspace/projects/${projectId}`), { headers: authHeaders() }).catch(() => {});
    }
  });
});
