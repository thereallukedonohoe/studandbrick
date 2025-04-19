import csv
import requests
from requests_oauthlib import OAuth1
from html import unescape

# BrickLink API credentials
auth = OAuth1(
    '8283C2FA185D4B23BF1EA7D594BEC386',
    'A6DEB6718DC34106B0F354A2899C69C4',
    '4594AC48B120458D8A798316A043D723',
    '7FA7BD09FB034CA09FCA9A542A24361D'
)

def get_inventory():
    r = requests.get("https://api.bricklink.com/api/store/v1/inventories?page=1", auth=auth)
    if r.status_code != 200:
        print("❌ Error fetching inventory")
        return []
    return r.json().get("data", [])[:5]  # ✅ Limit to 5 items for testing

def get_inventory_detail(inventory_id):
    r = requests.get(f"https://api.bricklink.com/api/store/v1/inventories/{inventory_id}", auth=auth)
    if r.status_code != 200:
        print(f"⚠️ Could not fetch detail for inventory ID {inventory_id}")
        return None
    return r.json().get("data", {})

def generate_feed():
    inventory = get_inventory()
    rows = []

    for item in inventory:
        inventory_id = item.get("inventory_id")
        detail = get_inventory_detail(inventory_id)
        if not detail:
            continue

        item_data = detail.get("item", {})
        item_no = item_data.get("no")
        item_name = unescape(item_data.get("name", ""))
        item_type = item_data.get("type")
        color_id = detail.get("color_id")
        color_name = detail.get("color_name")
        quantity = detail.get("quantity")
        condition = "Used" if detail.get("new_or_used") == "U" else "New"
        unit_price = f"{detail.get('unit_price')} AUD"

        image_link = f"https://img.bricklink.com/ItemImage/PN/{color_id}/{item_no}.png"
        link = f"https://store.bricklink.com/luke.donohoe#/shop?o={{\"q\":\"{inventory_id}\",\"sort\":0,\"pgSize\":100,\"showHomeItems\":0}}"

        rows.append({
            "id": inventory_id,
            "title": f"{color_name} {item_name}",
            "description": f"{item_type} {item_no}",
            "availability": "In Stock",
            "condition": condition,
            "price": unit_price,
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

    # GitHub Pages redirect
    with open("index.html", "w") as f:
        f.write("<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0; url=meta_product_feed.csv'></head><body></body></html>")

# Run it
if __name__ == "__main__":
    generate_feed()
