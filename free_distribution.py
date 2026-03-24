import requests
import json
import datetime

API_URL = "https://www.gamerpower.com/api/giveaways?platform=pc"
CACHE_FILE = "cache.json"
WEBHOOK = "<YOUR_WEBHOOK_URL>"   # ← あなたの Webhook を入れる

def send_to_discord(msg: str):
    requests.post(WEBHOOK, json={"content": msg})

def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    old = load_cache()
    old_ids = {g["id"] for g in old}

    res = requests.get(API_URL)
    games = res.json()

    # 今日追加された無料配布だけ抽出
    new_games = [g for g in games if g["id"] not in old_ids]

    # Discord へ通知
    for g in new_games:
        msg = (
            f"🎁 **無料ゲーム更新！**\n"
            f"**タイトル:** {g['title']}\n"
            f"**プラットフォーム:** {g['platforms']}\n"
            f"{g['open_giveaway_url']}"
        )
        send_to_discord(msg)

    # キャッシュ更新
    save_cache(games)

if __name__ == "__main__":
    main()
