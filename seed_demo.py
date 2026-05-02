"""Seed realistic demo data for dashboard testing. Run once."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, timezone
from core.database import (
    init_db, add_product, add_price_check, add_alert,
    update_product, get_product_by_url
)

init_db()

PRODUCTS = [
    {
        "url": "https://priceoye.pk/samsung-galaxy-s24-ultra",
        "name": "Samsung Galaxy S24 Ultra 256GB",
        "target": 249999,
    },
    {
        "url": "https://priceoye.pk/apple-iphone-15-pro-max",
        "name": "Apple iPhone 15 Pro Max 256GB",
        "target": 350000,
    },
    {
        "url": "https://www.sapphire.pk/products/lawn-unstitched-suit",
        "name": "Sapphire Summer Lawn Unstitched",
        "target": 3500,
    },
    {
        "url": "https://buyrawaha.com/products/urban-nomad-ombre",
        "name": "Urban Nomad – Impression of Ombré Nomade",
        "target": 6000,
    },
]

PRICE_SERIES = {
    "Samsung Galaxy S24 Ultra 256GB": [279999, 274999, 269999, 259999, 254999, 249999, 252000, 249999],
    "Apple iPhone 15 Pro Max 256GB":  [399999, 395000, 390000, 380000, 375000, 370000, 365000, 360000],
    "Sapphire Summer Lawn Unstitched": [4200, 3999, 3799, 3699, 3599, 3499, 3499, 3399],
    "Urban Nomad – Impression of Ombré Nomade": [7500, 7200, 6800, 6500, 6200, 5900, 5700, 5460],
}

AVAILABILITIES = ["In Stock", "In Stock", "In Stock", "Limited Stock",
                  "In Stock", "In Stock", "Out of Stock", "In Stock"]

now = datetime.now(timezone.utc)

for p in PRODUCTS:
    if get_product_by_url(p["url"]):
        print(f"Skipping (already exists): {p['name']}")
        continue

    pid = add_product(p["url"], p["target"])
    update_product(pid, name=p["name"])
    print(f"Added: {p['name']} (id={pid})")

    prices = PRICE_SERIES[p["name"]]
    for i, price in enumerate(prices):
        days_ago = len(prices) - 1 - i
        ts = (now - timedelta(days=days_ago * 2)).isoformat()
        avail = AVAILABILITIES[i]
        reasoning = (
            f"Found {price:,.0f} PKR as the main product price. "
            f"Several related items ({price + 5000:,.0f} and {price - 2000:,.0f}) "
            f"were visible in the 'Similar Products' section — ignored. "
            f"{'256GB variant selected.' if '256GB' in p['name'] else ''}"
        )
        from core.database import _conn
        check_id = add_price_check(pid, float(price), "PKR", "256GB" if "256GB" in p["name"] else None, avail, reasoning, None)
        # Patch the checked_at timestamp for realistic history
        with _conn() as con:
            con.execute("UPDATE price_checks SET checked_at=? WHERE id=?", (ts, check_id))

    # Add an alert for the last price drop
    final_price = prices[-1]
    prev_price  = prices[-2]
    if final_price <= p["target"]:
        drop_pct = ((prev_price - final_price) / prev_price) * 100
        add_alert(
            product_id=pid,
            alert_type="price_drop",
            old_price=float(prev_price),
            new_price=float(final_price),
            drop_pct=round(drop_pct, 2),
            message=f"Price dropped to {final_price:,.0f} PKR — target of {p['target']:,.0f} PKR reached!",
            sent_via="console",
        )
        print(f"  → Alert seeded for {p['name']}")

print("\nDemo data seeded successfully.")
