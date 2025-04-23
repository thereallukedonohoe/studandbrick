# category_scraper/scrape_categories.py
import csv
import asyncio
from playwright.async_api import async_playwright

OUTPUT_FILE = "category_scraper/output/categories.csv"

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.bricklink.com/catalogCategory.asp")

        results = []
        page_number = 1

        while True:
            print(f"Scraping page {page_number}")
            rows = await page.query_selector_all("table.catalog-category tbody tr")

            for row in rows[1:]:  # Skip header row
                cells = await row.query_selector_all("td")
                if len(cells) < 4:
                    continue
                cat_id = await cells[0].inner_text()
                name = await cells[1].inner_text()
                date_added = await cells[2].inner_text()
                cat_type = await cells[3].inner_text()

                results.append({
                    "Category ID": cat_id.strip(),
                    "Category Name": name.strip(),
                    "Date Added": date_added.strip(),
                    "Category Type": cat_type.strip()
                })

            next_button = await page.query_selector("a[title='Next Page']")
            if not next_button:
                break
            await next_button.click()
            await page.wait_for_timeout(1000)
            page_number += 1

        await browser.close()

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

if __name__ == "__main__":
    asyncio.run(scrape())
