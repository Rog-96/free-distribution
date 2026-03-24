import os
import json
import requests
from datetime import datetime, timezone

# ===== 設定 =====
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
CACHE_FILE = "cache.json"

# ===== 共通ユーティリティ =====
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {"steam": [], "epic": [], "fab": []}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def send_discord_message(platform, title, end_date):
    message = f"🎁 **{platform} で無料配布中！**\n" \
              f"**{title}**\n" \
              f"⏰ {end_date} まで"
    requests.post(WEBHOOK_URL, json={"content": message})


# =============================
#  Steam：期間限定無料の取得
# =============================
def fetch_steam_free_games():
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
                    "title": item.get("name"),
                    "end_date": end_dt.isoformat(),
                })

    return free_items


# =============================
#  Epic Games Store：期間限定無料
# =============================
def fetch_epic_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    r = requests.get(url)
    data = r.json()

    free_items = []
    elements = data["data"]["Catalog"]["searchStore"]["elements"]

    for game in elements:
        title = game["title"]
        promos = game.get("promotions")
        if not promos:
            continue

        upcoming = promos.get("promotionalOffers")
        if not upcoming:
            continue

        for offer in upcoming[0]["promotionalOffers"]:
            if offer["discountSetting"]["discountPercentage"] == 0:
                continue

            if offer["discountSetting"]["discountPercentage"] == 100:
                end_date = offer["endDate"]
                free_items.append({
                    "title": title,
                    "end_date": end_date,
                })

    return free_items


# =============================
#  Fab（旧 UE Marketplace）
#  GraphQL API：期間限定無料
# =============================
def fetch_fab_free_assets():
    url = "https://www.fab.com/graphql"
    query = """
    query {
      freeAssets {
        id
        title
        freeEndDate
      }
    }
    """

    r = requests.post(url, json={"query": query})
    data = r.json()

    free_items = []
    for asset in data["data"]["freeAssets"]:
        if asset["freeEndDate"]:  # 期間限定分だけ
            free_items.append({
                "title": asset["title"],
                "end_date": asset["freeEndDate"],
            })

    return free_items


# =============================
# メイン処理
# =============================
if __name__ == "__main__":
    cache = load_cache()

    # Steam
    steam_items = fetch_steam_free_games()
    for item in steam_items:
        if item["title"] not in cache["steam"]:
            send_discord_message("Steam", item["title"], item["end_date"])
            cache["steam"].append(item["title"])

    # Epic
    epic_items = fetch_epic_free_games()
    for item in epic_items:
        if item["title"] not in cache["epic"]:
            send_discord_message("Epic Games Store", item["title"], item["end_date"])
            cache["epic"].append(item["title"])

    # Fab
    fab_items = fetch_fab_free_assets()
    for item in fab_items:
        if item["title"] not in cache["fab"]:
            send_discord_message("Fab", item["title"], item["end_date"])
            cache["fab"].append(item["title"])

    save_cache(cache)
