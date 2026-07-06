const { test, expect } = require('@playwright/test');
const { login } = require('./helpers/auth');

test.describe('登录功能测试', () => {
  test('登录页面能正常显示', async ({ page }) => {
    await page.goto('/#/login');

    await expect(page.getByTestId('login-page')).toBeVisible();
    await expect(page.getByTestId('login-username-input')).toBeVisible();
    await expect(page.getByTestId('login-password-input')).toBeVisible();
    await expect(page.getByTestId('login-submit-button')).toBeVisible();
  });
});

test.describe('首页功能测试', () => {
  test('首页能正常加载或重定向到登录页', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('body')).not.toBeEmpty();
  });
});

test.describe('注册功能测试', () => {
  test('注册页面能正常显示', async ({ page }) => {
    await page.goto('/#/register');

    await expect(page.locator('form, .el-form').first()).toBeVisible();
    await expect(page.locator('input').first()).toBeVisible();
  });
});

test.describe('核心页面可访问性测试', () => {
  const corePages = [
    { path: '/learning-paths', name: '学习路径' },
    { path: '/exercises', name: '练习题库' },
    { path: '/exams', name: '考试中心' },
    { path: '/interview', name: '面试模拟' },
    { path: '/auto-test', name: '自动化测试' },
    { path: '/ai-tutor', name: 'AI导师' },
    { path: '/community', name: '社区' },
    { path: '/certificates', name: '证书' },
    { path: '/leaderboard', name: '排行榜' },
    { path: '/favorites', name: '收藏夹' },
  ];

  for (const pageInfo of corePages) {
    test(`${pageInfo.name}页面可访问或受登录保护`, async ({ page }) => {
      await page.goto(`/#${pageInfo.path}`);

      await expect(page.locator('body')).toBeVisible();
      await expect(page.locator('body')).not.toBeEmpty();
    });
  }
});

test.describe('API健康检查', () => {
  test('后端API能正常响应', async ({ request }) => {
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('页面导航测试', () => {
  test('登录成功后可以进入自动化测试页', async ({ page }) => {
    await login(page);
    await page.goto('/#/auto-test');

    await expect(page.getByTestId('auto-test-page')).toBeVisible();
  });
});

test.describe('响应式布局测试', () => {
  test('移动端登录页能正常显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/#/login');

    await expect(page.getByTestId('login-page')).toBeVisible();
    await expect(page.getByTestId('login-submit-button')).toBeVisible();
  });

  test('桌面端登录页能正常显示', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/#/login');

    await expect(page.getByTestId('login-page')).toBeVisible();
    await expect(page.getByTestId('login-submit-button')).toBeVisible();
  });
});
