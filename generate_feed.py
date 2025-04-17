import os
import csv
import requests
from requests_oauthlib import OAuth1
from html import unescape

# OAuth credentials
auth = OAuth1(
    os.environ['BL_CONSUMER_KEY'],
    os.environ['BL_CONSUMER_SECRET'],
    os.environ['BL_TOKEN_VALUE'],
    os.environ['BL_TOKEN_SECRET']
)

color_lookup = {
    0: "Black", 1: "Blue", 2: "Green", 3: "Dark Turquoise", 4: "Red", 5: "Dark Pink", 6: "Brown",
    7: "Tan", 8: "Yellow", 9: "White", 10: "Orange", 11: "Black", 12: "Gray", 13: "Light Blue",
    14: "Lime", 15: "Pink", 17: "Light Yellow", 18: "Purple", 19: "Blue-Violet", 20: "Dark Blue",
    21: "Light Green", 22: "Dark Green", 23: "Magenta", 25: "Very Light Orange", 26: "Turquoise",
    27: "Light Lime", 28: "Violet", 29: "Bright Pink", 30: "Light Gray", 31: "Very Light Gray",
    32: "Bright Light Blue", 33: "Rust", 34: "Bright Light Orange", 35: "Metallic Silver",
    36: "Metallic Gold", 38: "Pearl Light Gray", 39: "Dark Orange", 40: "Sand Red", 42: "Medium Blue",
    43: "Maersk Blue", 45: "Dark Red", 47: "Pearl Gold", 52: "Flat Silver", 57: "Flat Dark Gold",
    68: "Dark Tan", 69: "Reddish Brown", 70: "Bright Light Yellow", 71: "Dark Bluish Gray",
    72: "Light Bluish Gray", 73: "Medium Blue", 74: "Medium Green", 77: "Dark Bluish Gray",
    78: "Light Bluish Gray", 80: "Dark Brown", 88: "Dark Azure", 89: "Medium Azure",
    90: "Light Aqua", 91: "Lavender", 92: "Dark Lavender", 95: "Spring Yellowish Green",
    99: "Aqua", 110: "Bright Light Orange", 115: "Pearl Gold", 120: "Flat Silver"
}

type_labels = {"P": "Part", "M": "Minifig", "S": "Set"}

def get_inventory():
    all_items = []
    for page in range(1, 2):  # LIMIT TO 1 PAGE FOR TESTING
        url = f"https://api.bricklink.com/api/store/v1/inventories?page={page}"
        r = requests.get(url, auth=auth)
        if r.status_code != 200:
            print(f"❌ Failed to fetch page {page}")
            break
        page_items = r.json().get("data", [])
        if not page_items:
            break
        all_items.extend(page_items)
        print(f"🔁 Page {page} fetched with {len(page_items)} items.")
    return all_items

def get_inventory_detail(inventory_id):
    url = f"https://api.bricklink.com/api/store/v1/inventories/{inventory_id}"
    r = requests.get(url, auth=auth)
    if r.status_code == 200:
        return r.json().get("data", {})
    return {}

inventory = get_inventory()

with open("meta_product_feed.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "title", "description", "availability", "condition",
        "price", "link", "image_link", "brand", "google_product_category",
        "fb_product_category", "color", "quantity_to_sell_on_facebook"
    ])
    writer.writeheader()

    for item in inventory:
        part = item.get("item", {})
        part_no = part.get("no", "")
        part_type = part.get("type", "P")
        inventory_id = item.get("inventory_id")
        color_id = item.get("color_id")
        color = color_lookup.get(color_id, f"Color ID {color_id}")
        quantity = item.get("quantity", 0)
        price = f"{float(item['unit_price']):.2f} AUD" if item.get("unit_price") else ""
        condition = "New" if item["new_or_used"] == "N" else "Used (like new)"
        description = f"{type_labels.get(part_type, part_type)} - {part_no}"

        # Pull more detailed info if available
        detail = get_inventory_detail(inventory_id)
        name = unescape(detail.get("item", {}).get("name", "Unknown"))
        full_title = f"{color} {name}"

        # Image handling fallback
        standard_image = f"https://img.bricklink.com/ItemImage/PL/{color_id}/{part_no}.png"
        fallback_image = f"https://www.bricklink.com/catalogItemPic.asp?P={part_no}"

        # Storefront link
        link = f"https://store.bricklink.com/luke.donohoe#/shop?o={{\"q\":\"{inventory_id}\",\"sort\":0,\"pgSize\":100,\"showHomeItems\":0}}"

        writer.writerow({
            "id": inventory_id,
            "title": full_title,
            "description": description,
            "availability": "In Stock",
            "condition": condition,
            "price": price,
            "link": link,
            "image_link": standard_image,
            "brand": "Lego",
            "google_product_category": "3287",
            "fb_product_category": "47",
            "color": color,
            "quantity_to_sell_on_facebook": quantity
        })

with open("index.html", "w") as f:
    f.write("<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0; url=meta_product_feed.csv'></head><body></body></html>")
