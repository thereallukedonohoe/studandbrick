import asyncio
import json
import csv
from playwright.async_api import async_playwright

USERNAME = "luke.donohoe"
INPUT_FILE = "meta_product_feed.csv"
OUTPUT_FILE = "meta_product_feed_with_images.csv"

async def scrape_listing_data(playwright, inventory_id):
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    url = f"https://store.bricklink.com/{USERNAME}#/shop?o={json.dumps({'q': str(inventory_id)})}"
    await page.goto(url)
    await page.wait_for_selector(".itemBoxMain", timeout=15000)
    boxes = await page.query_selector_all(".itemBoxMain")

    for box in boxes:
        onclick_attr = await box.get_attribute("onclick")
        if onclick_attr and str(inventory_id) in onclick_attr:
            title_el = await box.query_selector("b")
            image_el = await box.query_selector("img")

            title = await title_el.inner_text() if title_el else "UNKNOWN"
            image_url = await image_el.get_attribute("src") if image_el else ""

            await browser.close()
            return {
                "title": title,
                "color": title.split()[0],
                "image_link": image_url
            }

    await browser.close()
    raise Exception(f"No matching listing found for inventory ID {inventory_id}")

async def run():
    with open(INPUT_FILE, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    updated = []
    async with async_playwright() as p:
        for row in rows[:5]:  # limit for now
            try:
                result = await scrape_listing_data(p, row["id"])
                row.update(result)
            except Exception as e:
                print(f"⚠️ Error on ID {row['id']}: {e}")
            updated.append(row)

    with open(OUTPUT_FILE, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=updated[0].keys())
        writer.writeheader()
        writer.writerows(updated)

asyncio.run(run())
