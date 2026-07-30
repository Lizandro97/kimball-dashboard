"""Take full-page screenshots with correct English hash routes."""
import asyncio
from playwright.async_api import async_playwright

PAGES = [
    ("overview",      "01-overview"),
    ("sales",         "02-ventas"),
    ("profitability", "03-rentabilidad"),
    ("customers",     "04-clientes"),
    ("shipping",      "05-envios"),
]

ML_TABS = [
    ("rfm",        "06-ml-rfm"),
    ("products",   "07-ml-products"),
    ("profit",     "08-ml-profit"),
    ("basket",     "09-ml-basket"),
    ("forecast",   "10-ml-forecast"),
    ("predictor",  "11-ml-predictor"),
]

async def screenshot_page(page, url, name):
    await page.goto(url, wait_until="networkidle", timeout=15000)
    await asyncio.sleep(3)
    for _ in range(30):
        plots = await page.locator(".js-plotly-plot, .kpi-card, .seg-card, .alert-card, table, .predictor-gauge").count()
        if plots > 3:
            break
        await asyncio.sleep(1)
    await asyncio.sleep(3)
    await page.screenshot(path=f"screenshots/{name}.png", full_page=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        for route, name in PAGES:
            await screenshot_page(page, f"http://localhost:8000/#{route}", name)

        await screenshot_page(page, "http://localhost:8000/#ml", "06-ml-rfm")

        for tab, name in ML_TABS[1:]:
            btn = page.locator(f"button.ml-tab[data-ml='{tab}']")
            if await btn.count() > 0:
                await btn.click()
                await asyncio.sleep(2)
                for _ in range(15):
                    plots = await page.locator(".js-plotly-plot, .kpi-card, .predictor-gauge, table").count()
                    if plots > 0:
                        break
                    await asyncio.sleep(1)
                await asyncio.sleep(3)
            await page.screenshot(path=f"screenshots/{name}.png", full_page=True)

        await browser.close()

asyncio.run(main())
