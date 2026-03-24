import os
import json
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
CACHE_FILE = "cache_fab.json"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def send(title, end_date):
    msg = f"🎁 **Fab で無料アセット配布中！**\n" \
          f"**{title}**\n" \
          f"⏰ {end_date} まで"
    requests.post(WEBHOOK_URL, json={"content": msg})


def fetch_fab():
    url = "https://www.fab.com/free"
    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")
    items = []

    for article in soup.find_all("article"):
        title_tag = article.find("h3")
        if not title_tag:
            continue

        title = title_tag.text.strip()

        end_date = None
        end_span = article.find("span", {"data-testid": "free-end-date"})
        if end_span:
            end_date = end_span.text.strip()

        # 終了日が無い＝常時無料 → 除外
        if not end_date:
            continue

        items.append({"title": title, "end_date": end_date})

    return items


if __name__ == "__main__":
    cache = load_cache()

    for item in fetch_fab():
        if item["title"] not in cache:
            send(item["title"], item["end_date"])
            cache.append(item["title"])

    save_cache(cache)
