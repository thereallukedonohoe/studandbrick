import os
import csv
import requests
from requests_oauthlib import OAuth1
from html import unescape

# OAuth credentials (update if needed)
auth = OAuth1(
    os.environ['BL_CONSUMER_KEY'],
    os.environ['BL_CONSUMER_SECRET'],
    os.environ['BL_TOKEN_VALUE'],
    os.environ['BL_TOKEN_SECRET']
)

type_labels = {"P": "Part", "M": "Minifig", "S": "Set"}

def get_inventory():
    all_items = []
    for page in range(1, 2):  # Limit to 1 page for testing
        r = requests.get(f"https://api.bricklink.com/api/store/v1/inventories?page={page}", auth=auth)
        if r.status_code != 200:
            print(f"❌ Error fetching page {page}: {r.status_code}")
            break
        items = r.json().get("data", [])
        all_items.extend(items)
        print(f"📦 Page {page} fetched ({len(items)} items)")
    return all_items

def get_inventory_detail(inventory_id):
    r = requests.get(f"https://api.bricklink.com/api/store/v1/inventories/{inventory_id}", auth=auth)
    if r.status_code != 200:
        return None
    return r.json().get("data", {})

def safe_price(value):
    try:
        return f"{float(value):.2f} AUD"
    except Exception:
        return ""

inventory = get_inventory()

with open("meta_product_feed.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "title", "description", "availability", "condition",
        "price", "link", "image_link", "brand", "google_product_category",
        "fb_product_category", "color", "quantity_to_sell_on_facebook"
    ])
    writer.writeheader()

    for item in inventory:
        inventory_id = item.get("inventory_id")
        detail = get_inventory_detail(inventory_id)
        if not detail:
            print(f"⚠️ Skipping {inventory_id} — detail fetch failed")
            continue

        part = detail.get("item", {})
        part_no = part.get("no", "")
        part_type = part.get("type", "P")
        name_raw = part.get("name", "")
        name = unescape(name_raw)
        color_name = detail.get("color_name", "Unknown")
        quantity = detail.get("quantity", 0)
        condition = "New" if detail.get("new_or_used") == "N" else "Used (like new)"
        price = safe_price(detail.get("unit_price"))
        description = f"{type_labels.get(part_type, part_type)} - {part_no}"
        title = f"{color_name} {name}"

        link = f"https://store.bricklink.com/luke.donohoe#/shop?o={{\"q\":\"{inventory_id}\",\"sort\":0,\"pgSize\":100,\"showHomeItems\":0}}"

        writer.writerow({
            "id": inventory_id,
            "title": title,
            "description": description,
            "availability": "In Stock",
            "condition": condition,
            "price": price,
            "link": link,
            "image_link": "N/A",
            "brand": "Lego",
            "google_product_category": "3287",
            "fb_product_category": "47",
            "color": color_name,
            "quantity_to_sell_on_facebook": quantity
        })

with open("index.html", "w") as f:
    f.write("<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0; url=meta_product_feed.csv'></head><body></body></html>")
