import os
import json
import requests
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
CACHE_FILE = "cache_steam_epic.json"

# ===== Utility =====
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {"steam": [], "epic": []}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def send(platform, title, end_date):
    msg = f"🎁 **{platform} で無料配布中！**\n" \
          f"**{title}**\n" \
          f"⏰ {end_date} まで"
    requests.post(WEBHOOK_URL, json={"content": msg})


# =============================
# Steam：期間限定無料
# =============================
def fetch_steam():
    url = "https://store.steampowered.com/api/featuredcategories"
    r = requests.get(url)
    data = r.json()

    free_items = []
    specials = data.get("specials", {}).get("items", [])

    for item in specials:
        if item.get("discount_percent") == 100:
            end_time = item.get("discount_expiration")
            if end_time:
                end_dt = datetime.fromtimestamp(end_time, timezone.utc)
                free_items.append({
                    "title": item["name"],
                    "end_date": end_dt.isoformat()
                })

    return free_items


# =============================
# Epic：期間限定無料
# =============================
def fetch_epic():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    r = requests.get(url)
    data = r.json()

    free_items = []
    elements = data["data"]["Catalog"]["searchStore"]["elements"]

    for game in elements:
        promos = game.get("promotions")
        if not promos:
            continue

        offers = promos.get("promotionalOffers")
        if not offers:
            continue

        for offer in offers[0]["promotionalOffers"]:
            if offer["discountSetting"]["discountPercentage"] == 100:
                free_items.append({
                    "title": game["title"],
                    "end_date": offer["endDate"],
                })

    return free_items


# =============================
# Main
# =============================
if __name__ == "__main__":
    cache = load_cache()

    # Steam
    for item in fetch_steam():
        if item["title"] not in cache["steam"]:
            send("Steam", item["title"], item["end_date"])
            cache["steam"].append(item["title"])

    # Epic
    for item in fetch_epic():
        if item["title"] not in cache["epic"]:
            send("Epic Games Store", item["title"], item["end_date"])
            cache["epic"].append(item["title"])

    save_cache(cache)
