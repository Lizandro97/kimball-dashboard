"""Take screenshots of each dashboard module for the README."""
import asyncio
from playwright.async_api import async_playwright

PAGES = [
    ("overview",  "01-overview"),
    ("ventas",    "02-ventas"),
    ("rentabilidad", "03-rentabilidad"),
    ("clientes",  "04-clientes"),
    ("envios",    "05-envios"),
]

ML_TABS = [
    ("rfm",        "06-ml-rfm"),
    ("products",   "07-ml-products"),
    ("profit",     "08-ml-profit"),
    ("basket",     "09-ml-basket"),
    ("forecast",   "10-ml-forecast"),
    ("predictor",  "11-ml-predictor"),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        for route, name in PAGES:
            await page.goto(f"http://localhost:8000/#{route}", wait_until="networkidle")
            await asyncio.sleep(3)
            await page.screenshot(path=f"screenshots/{name}.png", full_page=False)

        # ML page with different tabs
        await page.goto("http://localhost:8000/#ml", wait_until="networkidle")
        await asyncio.sleep(3)

        for tab, name in ML_TABS:
            btn = page.locator(f"button.ml-tab[data-ml='{tab}']")
            if await btn.count() > 0:
                await btn.click()
                await asyncio.sleep(3)
            await page.screenshot(path=f"screenshots/{name}.png", full_page=False)

        await browser.close()

asyncio.run(main())
