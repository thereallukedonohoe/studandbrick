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
    print(f"🌐 Visiting: {url}")
    await page.goto(url)
    try:
        await page.wait_for_selector(".itemBoxMain", timeout=20000)
    except Exception:
        print(f"❌ No item boxes found for {inventory_id}")
        await browser.close()
        return None

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

    print(f"⚠️ No matching listing found for inventory ID {inventory_id}")
    await browser.close()
    return None

async def run():
    with open(INPUT_FILE, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    updated = []
    async with async_playwright() as p:
        for row in rows[:5]:  # LIMIT to 5 for testing
            result = await scrape_listing_data(p, row["id"])
            if result:
                row.update(result)
            else:
                print(f"⚠️ Skipping row for ID {row['id']}")
            updated.append(row)

    if not any("title" in row and row["title"] != "PLACEHOLDER" for row in updated):
        print("⚠️ No listings were successfully scraped. Skipping file write.")
        return

    with open(OUTPUT_FILE, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=updated[0].keys())
        writer.writeheader()
        writer.writerows(updated)

asyncio.run(run())
