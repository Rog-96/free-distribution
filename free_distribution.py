import requests
import json
from datetime import datetime, timedelta, timezone

API_URL = "https://www.gamerpower.com/api/giveaways?platform=pc"
CACHE_FILE = "cache.json"
WEBHOOK = "https://discord.com/api/webhooks/1486093731160522924/avUMB-X0mzYScMSX09Dpb4fx4Uj7GXMJFt3rJKMXTZD3Yf803aF5FTK0V_si5rgwHkkr"

# 日本語曜日
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

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

def parse_platform(platforms: str):
    text = platforms.lower()
    if "epic" in text:
        return "Epic"
    if "steam" in text:
        return "Steam"
    return "PC"  # その他（例: GOG 等）

def format_end_date(iso_str: str):
    try:
        # 例: "2025-02-15 00:00:00"
        dt = datetime.strptime(iso_str, "%Y-%m-%d %H:%M:%S")

        # API は UTC 前提なので JST に変換
        JST = timezone(timedelta(hours=9))
        dt = dt.replace(tzinfo=timezone.utc).astimezone(JST)

        weekday = WEEKDAYS[dt.weekday()]
        return dt.strftime(f"%m月%d日（{weekday}）%H時まで")
    except:
        return "期限不明"

def main():
    old = load_cache()
    old_ids = {g["id"] for g in old}

    games = requests.get(API_URL).json()
    new_games = [g for g in games if g["id"] not in old_ids]

    for g in new_games:
        platform = parse_platform(g["platforms"])
        end_time = format_end_date(g.get("end_date", ""))

        msg = (
            f"🎁 **{platform} で無料配布中！**\n"
            f"**{g['title']}**\n"
            f"{end_time}\n"
            f"{g['open_giveaway_url']}"
        )

        send_to_discord(msg)

    save_cache(games)

if __name__ == "__main__":
    main()
