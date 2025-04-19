import csv
import asyncio
import aiohttp
import requests
from requests_oauthlib import OAuth1
from html import unescape

# BrickLink API credentials
CONSUMER_KEY = '8283C2FA185D4B23BF1EA7D594BEC386'
CONSUMER_SECRET = 'A6DEB6718DC34106B0F354A2899C69C4'
TOKEN_VALUE = '4594AC48B120458D8A798316A043D723'
TOKEN_SECRET = '7FA7BD09FB034CA09FCA9A542A24361D'

API_BASE = "https://api.bricklink.com/api/store/v1"

# Fix: Generate a clean Authorization header for aiohttp
def get_auth_header(url):
    from requests_oauthlib.oauth1_auth import SIGNATURE_TYPE_AUTH_HEADER
    oauth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, TOKEN_VALUE, TOKEN_SECRET, signature_type=SIGNATURE_TYPE_AUTH_HEADER)
    dummy = requests.Request('GET', url).prepare()
    signed = oauth(dummy)
    return {'Authorization': signed.headers['Authorization']}

async def fetch_inventory():
    url = f"{API_BASE}/inventories?page=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=get_auth_header(url)) as r:
            if r.status != 200:
                print("❌ Failed to fetch inventory list")
                return []
            data = await r.json()
            return data.get("data", [])

async def fetch_item_detail(session, inventory_id):
    url = f"{API_BASE}/inventories/{inventory_id}"
    try:
        async with session.get(url, headers=get_auth_header(url)) as r:
            if r.status != 200:
                return None
            detail = await r.json()
            return detail.get("data", {})
    except Exception:
        return None

async def generate_feed():
    inventory = await fetch_inventory()
    rows = []

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_item_detail(session, item.get("inventory_id")) for item in inventory]
        details = await asyncio.gather(*tasks)

        for detail in details:
            if not detail:
                continue
            if detail.get("is_stock_room") is not False:
                continue
            try:
                unit_price_val = float(detail.get("unit_price"))
            except (ValueError, TypeError):
                continue
            if unit_price_val < 1.00:
                continue

            item_data = detail.get("item", {})
            item_no = item_data.get("no")
            item_name = unescape(item_data.get("name", ""))
            item_type = item_data.get("type")
            color_id = detail.get("color_id")
            color_name = detail.get("color_name")
            quantity = detail.get("quantity")
            condition = "Used" if detail.get("new_or_used") == "U" else "New"
            price = f"{unit_price_val:.2f} AUD"
            image_link = f"https://img.bricklink.com/ItemImage/PN/{color_id}/{item_no}.png"
            link = f"https://store.bricklink.com/luke.donohoe#/shop?o={{\"q\":\"{detail['inventory_id']}\",\"sort\":0,\"pgSize\":100,\"showHomeItems\":0}}"

            rows.append({
                "id": detail["inventory_id"],
                "title": f"{color_name} {item_name}",
                "description": f"{item_type} {item_no}",
                "availability": "In Stock",
                "condition": condition,
                "price": price,
                "link": link,
                "image_link": image_link,
                "brand": "Lego",
                "google_product_category": "3287",
                "fb_product_category": "47",
                "color": color_name,
                "quantity_to_sell_on_facebook": quantity
            })

    # Write to CSV
    with open("meta_product_feed.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "description", "availability", "condition",
            "price", "link", "image_link", "brand", "google_product_category",
            "fb_product_category", "color", "quantity_to_sell_on_facebook"
        ])
        writer.writeheader()
        writer.writerows(rows)

    # Write redirect
    with open("index.html", "w") as f:
        f.write("<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0; url=meta_product_feed.csv'></head><body></body></html>")

if __name__ == "__main__":
    asyncio.run(generate_feed())
