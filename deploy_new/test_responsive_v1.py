"""多视口响应式测试: CaseList 和 JMeter 在不同屏幕尺寸下的布局."""
import asyncio
import os
from playwright.async_api import async_playwright

URL_BASE = "http://35.189.163.24"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# 关键视口
VIEWPORTS = [
    {"name": "1920x1080", "w": 1920, "h": 1080},  # 全屏桌面
    {"name": "1600x900",  "w": 1600, "h": 900},   # 标屏
    {"name": "1440x900",  "w": 1440, "h": 900},   # 笔记本
    {"name": "1366x768",  "w": 1366, "h": 768},   # 低端笔记本
    {"name": "1280x800",  "w": 1280, "h": 800},   # Mac 小屏
    {"name": "1024x768",  "w": 1024, "h": 768},   # 平板横屏
    {"name": "768x1024",  "w": 768,  "h": 1024},  # 平板竖屏
]


async def login_and_get_token(ctx):
    resp = await ctx.request.post(f"{URL_BASE}/api/v1/auth/login", data={
        "username": "admin", "password": "Admin@2026!Secure"
    })
    body = await resp.json()
    return body.get("access_token")


async def measure_layout(page, layout_sel):
    return await page.evaluate(f"""
        () => {{
          const layout = document.querySelector('{layout_sel}')
          if (!layout) return null
          const r = layout.getBoundingClientRect()
          const children = Array.from(layout.children).filter(c => c.offsetParent !== null && !c.classList.contains('base-splitter')).map(c => ({{
            cls: c.className,
            w: c.getBoundingClientRect().width,
            h: c.getBoundingClientRect().height,
          }}))
          const sps = Array.from(layout.querySelectorAll('.base-splitter'))
          return {{
            layoutW: r.width,
            layoutH: r.height,
            visibleChildren: children.length,
            children,
            splitterCount: sps.length,
            splitterVisible: sps.filter(s => s.offsetParent !== null).length,
          }}
        }}
    """)


async def test_caselist(ctx, page, viewport, out_dir):
    name, w, h = viewport["name"], viewport["w"], viewport["h"]
    print(f"\n--- CaseList @ {name} ---")
    await page.set_viewport_size({"width": w, "height": h})
    await page.goto(f"{URL_BASE}/", wait_until="load", timeout=30000)
    await page.wait_for_timeout(1500)
    await page.evaluate("() => { window.location.hash = '#/auto-test'; }")
    await page.wait_for_timeout(2000)
    # 切换到接口库 tab
    try:
        await page.click("text=接口库", timeout=8000)
        await page.wait_for_timeout(2000)
    except Exception:
        pass
    # 等待组件加载
    try:
        await page.wait_for_selector(".case-list-layout", state="visible", timeout=8000)
    except Exception as e:
        print(f"  layout not visible: {e}")
        await page.screenshot(path=os.path.join(out_dir, f"caselist-{name}-fail.png"))
        return None

    info = await measure_layout(page, ".case-list-layout")
    print(f"  layout: {info['layoutW']:.0f}x{info['layoutH']:.0f} children={info['visibleChildren']} splitters={info['splitterVisible']}")
    for c in info["children"]:
        print(f"    - {c['cls'][:40]}: {c['w']:.0f}px")
    await page.screenshot(path=os.path.join(out_dir, f"caselist-{name}.png"), full_page=False)
    return info


async def test_jmeter_step1(ctx, page, viewport, out_dir):
    name, w, h = viewport["name"], viewport["w"], viewport["h"]
    print(f"\n--- JMeter Step1 @ {name} ---")
    await page.set_viewport_size({"width": w, "height": h})
    await page.goto(f"{URL_BASE}/", wait_until="load", timeout=30000)
    await page.wait_for_timeout(1500)
    await page.evaluate("() => { window.location.hash = '#/jmeter-assistant'; }")
    await page.wait_for_timeout(3000)
    try:
        await page.wait_for_selector(".step1-layout", state="visible", timeout=8000)
    except Exception as e:
        print(f"  step1 not visible: {e}")
        await page.screenshot(path=os.path.join(out_dir, f"jmeter1-{name}-fail.png"))
        return None
    info = await measure_layout(page, ".step1-layout")
    print(f"  layout: {info['layoutW']:.0f}x{info['layoutH']:.0f} children={info['visibleChildren']} splitters={info['splitterVisible']}")
    for c in info["children"]:
        print(f"    - {c['cls'][:40]}: {c['w']:.0f}px")
    await page.screenshot(path=os.path.join(out_dir, f"jmeter1-{name}.png"), full_page=False)
    return info


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        out_dir = os.path.join(OUT_DIR, "responsive_v1")
        os.makedirs(out_dir, exist_ok=True)

        # 单 context 复用 token
        ctx = await browser.new_context(viewport={"width": 1600, "height": 900})
        token = await login_and_get_token(ctx)
        print(f"token: {token[:30]}...")
        await ctx.add_init_script(f"""
            localStorage.setItem('token', '{token}');
            // 清空 splitter 持久化，让所有视口都从默认宽度开始
            Object.keys(localStorage).filter(k => k.startsWith('tm-caselist-')).forEach(k => localStorage.removeItem(k));
            Object.keys(localStorage).filter(k => k.startsWith('tm-jmeter-')).forEach(k => localStorage.removeItem(k));
        """)

        page = await ctx.new_page()
        page.on("pageerror", lambda err: print(f"  [PAGEERROR] {str(err)[:150]}"))

        # ============ CaseList 多视口 ============
        print("\n========= CaseList 多视口 =========")
        caselist_results = []
        for vp in VIEWPORTS:
            info = await test_caselist(ctx, page, vp, out_dir)
            if info:
                caselist_results.append((vp, info))

        # ============ JMeter Step1 多视口 ============
        print("\n========= JMeter Step1 多视口 =========")
        jmeter_results = []
        for vp in VIEWPORTS:
            info = await test_jmeter_step1(ctx, page, vp, out_dir)
            if info:
                jmeter_results.append((vp, info))

        # ============ 汇总报告 ============
        print("\n\n========= 响应式布局汇总 =========")
        print(f"{'Viewport':<12} {'CaseList W':<12} {'JMeter W':<12}")
        for vp in VIEWPORTS:
            cl = next((info['layoutW'] for v, info in caselist_results if v['name'] == vp['name']), 0)
            jm = next((info['layoutW'] for v, info in jmeter_results if v['name'] == vp['name']), 0)
            print(f"{vp['name']:<12} {cl:<12.0f} {jm:<12.0f}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
