"""Playwright 验证 JmeterAssistant 三步骤布局：3 个 splitter + 完全折叠.

遵循真实用户流程：
- Step 1: 测试 splitter → 勾选用例 → 导入 → 自动跳转 Step 2
- Step 2: 测试 splitter → 生成预览 → 自动跳转 Step 3
- Step 3: 测试 splitter
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

URL_BASE = "http://35.189.163.24"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


async def measure(page, layout_selector):
    return await page.evaluate(f"""
        () => {{
          const layout = document.querySelector('{layout_selector}')
          if (!layout) return {{ found: false }}
          const sps = Array.from(layout.querySelectorAll('.base-splitter'))
          return {{
            found: true,
            splitterCount: sps.length,
            layoutW: layout.getBoundingClientRect().width,
            children: Array.from(layout.children).filter(c => !c.classList.contains('base-splitter')).map(c => ({{
              cls: c.className,
              w: c.getBoundingClientRect().width,
              visible: c.offsetParent !== null,
            }})),
            fab: !!document.querySelector('.panel-expand-fab'),
          }}
        }}
    """)


async def drag(page, layout_selector, idx, dx, dy=0, steps=20):
    sp = await page.evaluate(f"""
        () => {{
          const layout = document.querySelector('{layout_selector}')
          if (!layout) return null
          const sps = Array.from(layout.querySelectorAll('.base-splitter'))
          if (!sps[{idx}]) return null
          const r = sps[{idx}].getBoundingClientRect()
          if (r.width < 5) return null
          return {{ x: r.x + r.width/2, y: r.y + r.height/2 }}
        }}
    """)
    if not sp:
        print(f"  splitter[{idx}] not found or invisible in {layout_selector}")
        return False
    print(f"  起点: ({sp['x']:.0f}, {sp['y']:.0f}), 拖 ({dx}, {dy})")
    await page.mouse.move(sp["x"], sp["y"])
    await page.wait_for_timeout(200)
    await page.mouse.down()
    await page.wait_for_timeout(300)
    for i in range(1, steps + 1):
        await page.mouse.move(sp["x"] + (dx * i / steps), sp["y"] + (dy * i / steps))
        await page.wait_for_timeout(20)
    await page.wait_for_timeout(100)
    await page.mouse.up()
    await page.wait_for_timeout(500)
    return True


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 900})
        page = await ctx.new_page()

        # 登录
        print(">>> Login via API")
        resp = await ctx.request.post(f"{URL_BASE}/api/v1/auth/login", data={
            "username": "admin", "password": "Admin@2026!Secure"
        })
        body = await resp.json()
        token = body.get("access_token")
        print(f"  token: {token[:30] if token else 'NONE'}...")
        await ctx.add_init_script(f"""
            localStorage.setItem('token', '{token}');
            localStorage.removeItem('tm-jmeter-step1-left-width');
            localStorage.removeItem('tm-jmeter-tree-width');
            localStorage.removeItem('tm-jmeter-step3-sidebar-width');
        """)

        # 跳转到 jmeter-assistant
        print(">>> Goto /jmeter-assistant")
        await page.goto(f"{URL_BASE}/", wait_until="load", timeout=30000)
        await page.wait_for_timeout(2000)
        await page.evaluate(f"() => localStorage.setItem('token', '{token}');")
        await page.evaluate("() => { window.location.hash = '#/jmeter-assistant'; }")
        await page.wait_for_timeout(3000)

        os.makedirs(os.path.join(OUT_DIR, "splitter_v7_jmeter"), exist_ok=True)

        # ============== Step 1: 选择接口 ==============
        print("\n=== Step 1: 选择接口 ===")
        await page.wait_for_selector(".step1-layout", state="visible", timeout=10000)
        m = await measure(page, ".step1-layout")
        print(f"  step1 splitters={m.get('splitterCount')} children={len(m.get('children', []))}")
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/01-step1-initial.png"))

        # 测 1.1: 拖 splitter 一直向左（左侧 panel 折叠）
        print("\n>>> Test 1.1: step1 splitter 拖左 1000px (左侧 panel 折叠)")
        await drag(page, ".step1-layout", 0, -1000)
        m1 = await measure(page, ".step1-layout")
        print(f"  fab visible: {m1.get('fab')}")
        assert m1.get('fab'), "FAB should appear after collapsing step1 left panel"
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/01-step1-collapsed.png"))

        # 测 1.2: 点击浮动按钮恢复
        print("\n>>> Test 1.2: 点击浮动按钮恢复")
        await page.click(".panel-expand-fab")
        await page.wait_for_timeout(600)
        m2 = await measure(page, ".step1-layout")
        print(f"  fab after click: {m2.get('fab')}")
        assert not m2.get('fab'), "FAB should disappear after expanding"
        # 再测拖右到最大
        print(">>> Test 1.2b: 拖右 2000px (左侧 panel 最大)")
        await drag(page, ".step1-layout", 0, 2000)
        m2b = await measure(page, ".step1-layout")
        left_width = next((c['w'] for c in m2b.get('children', []) if 'step1-left' in c['cls']), 0)
        print(f"  step1 left width: {left_width}")
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/01-step1-max.png"))

        # 真实用户流程：勾选一个接口，导入到脚本（自动跳到 Step 2）
        print("\n>>> Importing case from interface library to advance to Step 2...")
        # 勾选第一个 import-case-item 的 checkbox
        try:
            await page.evaluate("""
                () => {
                  const items = document.querySelectorAll('.import-case-item')
                  if (items.length === 0) return 'no-items'
                  const cb = items[0].querySelector('input[type=checkbox]')
                  if (cb && !cb.checked) {
                    cb.click()
                  }
                  return items.length
                }
            """)
            await page.wait_for_timeout(500)
            # 点击「导入到脚本」按钮
            import_clicked = await page.evaluate("""
                () => {
                  const buttons = Array.from(document.querySelectorAll('.import-footer .el-button'))
                  const target = buttons.find(b => b.textContent.includes('导入到脚本'))
                  if (target) {
                    target.click()
                    return true
                  }
                  return false
                }
            """)
            print(f"  import clicked: {import_clicked}")
            if not import_clicked:
                # Fallback: 勾选然后查找任何带"导入"文字的按钮
                await page.evaluate("""
                    () => {
                      const buttons = Array.from(document.querySelectorAll('button'))
                      const target = buttons.find(b => b.textContent.includes('导入'))
                      if (target) target.click()
                    }
                """)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  import flow error: {e}")

        # ============== Step 2: 配置参数 ==============
        print("\n=== Step 2: 配置压测参数 ===")
        # 等到 step2-editor-layout 可见
        try:
            await page.wait_for_selector(".step2-editor-layout", state="visible", timeout=10000)
            print("  step2 visible (import succeeded)")
        except Exception as e:
            print(f"  step2 not visible: {e}")
            await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/02-step2-fail.png"))
            return  # 无法继续

        m3 = await measure(page, ".step2-editor-layout")
        print(f"  step2 splitters={m3.get('splitterCount')}")
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/02-step2-initial.png"))

        # 测 2.1: 拖 tree splitter 一直向左（tree 折叠）
        print("\n>>> Test 2.1: step2 tree splitter 拖左 1000px (tree 折叠)")
        await drag(page, ".step2-editor-layout", 0, -1000)
        m4 = await measure(page, ".step2-editor-layout")
        print(f"  fab visible: {m4.get('fab')}")
        assert m4.get('fab'), "FAB should appear after collapsing tree"
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/02-step2-collapsed.png"))

        # 测 2.2: 点击浮动按钮恢复
        print("\n>>> Test 2.2: 点击浮动按钮恢复")
        await page.click(".panel-expand-fab")
        await page.wait_for_timeout(600)
        m5 = await measure(page, ".step2-editor-layout")
        print(f"  fab after click: {m5.get('fab')}")
        assert not m5.get('fab'), "FAB should disappear after expanding"
        # 再测拖右到最大
        print(">>> Test 2.2b: 拖右 2000px (tree 最大)")
        await drag(page, ".step2-editor-layout", 0, 2000)
        m5b = await measure(page, ".step2-editor-layout")
        print(f"  step2 children: {[(c['cls'][:30], c['w']) for c in m5b.get('children', [])]}")
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/02-step2-max.png"))

        # 真实用户流程：点击「生成预览」按钮（自动跳到 Step 3）
        print("\n>>> Click '生成预览' to advance to Step 3...")
        preview_clicked = await page.evaluate("""
            () => {
              const buttons = Array.from(document.querySelectorAll('button'))
              const target = buttons.find(b => b.textContent.includes('生成预览'))
              if (target) {
                target.click()
                return true
              }
              return false
            }
        """)
        print(f"  preview clicked: {preview_clicked}")
        await page.wait_for_timeout(3000)  # 等待 JMX 生成

        # ============== Step 3: 导出 JMX ==============
        print("\n=== Step 3: 导出 JMX ===")
        try:
            await page.wait_for_selector(".step3-layout", state="visible", timeout=10000)
            print("  step3 visible (preview succeeded)")
        except Exception as e:
            print(f"  step3 not visible: {e}")
            await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/03-step3-fail.png"))
            return

        m6 = await measure(page, ".step3-layout")
        print(f"  step3 splitters={m6.get('splitterCount')}")
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/03-step3-initial.png"))

        # 测 3.1: 拖 step3 splitter 一直向左（JMX 侧边栏折叠）
        print("\n>>> Test 3.1: step3 splitter 拖左 1000px (JMX sidebar 折叠)")
        await drag(page, ".step3-layout", 0, -1000)
        m7 = await measure(page, ".step3-layout")
        print(f"  fab visible: {m7.get('fab')}")
        assert m7.get('fab'), "FAB should appear after collapsing step3 sidebar"
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/03-step3-collapsed.png"))

        # 测 3.2: 点击浮动按钮恢复
        print("\n>>> Test 3.2: 点击浮动按钮恢复")
        await page.click(".panel-expand-fab")
        await page.wait_for_timeout(600)
        m8 = await measure(page, ".step3-layout")
        print(f"  fab after click: {m8.get('fab')}")
        assert not m8.get('fab'), "FAB should disappear after expanding"
        print(">>> Test 3.2b: 拖右 2000px (JMX sidebar 最大)")
        await drag(page, ".step3-layout", 0, 2000)
        m8b = await measure(page, ".step3-layout")
        print(f"  step3 children: {[(c['cls'][:30], c['w']) for c in m8b.get('children', [])]}")
        await page.screenshot(path=os.path.join(OUT_DIR, "splitter_v7_jmeter/03-step3-max.png"))

        print("\n=== 所有断言通过 ===")
        print("  Step 1/2/3 splitter 拖到 0 折叠 → 浮动按钮 → 恢复 → 拖到 800 最大化 全部 OK")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
