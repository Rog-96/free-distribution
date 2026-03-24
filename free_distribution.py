import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
CACHE_FILE = "cache.json"


# ===== Utility =====
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {"steam": [], "epic": [], "fab": []}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def send_discord_message(platform, title, end_date):
    msg = f"🎁 **{platform} で無料配布中！**\n" \
          f"**{title}**\n" \
          f"⏰ {end_date} まで"
    requests.post(WEBHOOK_URL, json={"content": msg})


# =============================
# Steam（期間限定無料）
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
                    "title": item["name"],
                    "end_date": end_dt.isoformat()
                })

    return free_items


# =============================
# Epic Games Store（期間限定無料）
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

        offers = promos.get("promotionalOffers")
        if not offers:
            continue

        for offer in offers[0]["promotionalOffers"]:
            if offer["discountSetting"]["discountPercentage"] == 100:
                free_items.append({
                    "title": title,
                    "end_date": offer["endDate"]
                })

    return free_items


# =============================
# Fab（無料ページスクレイピング）
# =============================
def fetch_fab_free_assets():
    url = "https://www.fab.com/free"
    r = requests.get(url)

    # Fab のHTMLをパース
    soup = BeautifulSoup(r.text, "html.parser")

    items = []

    # Fab の無料アセットは <article> タグで列挙されている
    for article in soup.find_all("article"):
        title_tag = article.find("h3")
        if not title_tag:
            continue

        title = title_tag.text.strip()

        # 終了日情報が data-free-end などで埋め込まれているケースが多い
        end_date = None

        end_span = article.find("span", {"data-testid": "free-end-date"})
        if end_span:
            end_date = end_span.text.strip()

        # もしくは class から拾う
        if not end_date:
            for span in article.find_all("span"):
                if "Free until" in span.text:
                    end_date = span.text.replace("Free until", "").strip()
                    break

        # 終了日がない＝常時無料 → スキップ
        if not end_date:
            continue

        items.append({
            "title": title,
            "end_date": end_date
        })

    return items


# =============================
# Main
# =============================
if __name__ == "__main__":
    cache = load_cache()

    # Steam
    for item in fetch_steam_free_games():
        if item["title"] not in cache["steam"]:
            send_discord_message("Steam", item["title"], item["end_date"])
            cache["steam"].append(item["title"])

    # Epic
    for item in fetch_epic_free_games():
        if item["title"] not in cache["epic"]:
            send_discord_message("Epic Games Store", item["title"], item["end_date"])
            cache["epic"].append(item["title"])

    # Fab（スクレイピング）
    for item in fetch_fab_free_assets():
        if item["title"] not in cache["fab"]:
            send_discord_message("Fab", item["title"], item["end_date"])
            cache["fab"].append(item["title"])

    save_cache(cache)
