import os
import sys
from dotenv import load_dotenv
from api_client import PerplexityClient
from notifier import DiscordNotifier
from trend_history import TrendHistory
import datetime
import json

# Load environment variables
load_dotenv()

CONFIG_FILE = "bot_config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "search_category": "Dev Tools, PKM, Privacy Browsers, & Student Deals",
            "target_languages": "TypeScript, PHP, AWS, Rust, Go, New AI Tools",
            "excluded_keywords": ""
        }

LAST_RUN_FILE = "last_run.txt"

def has_run_today():
    try:
        if os.path.exists(LAST_RUN_FILE):
            with open(LAST_RUN_FILE, "r", encoding="utf-8") as f:
                last_run_date = f.read().strip()
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            return last_run_date == current_date
    except Exception as e:
        print(f"Warning: Could not check last run file: {e}")
    return False

def mark_as_run_today():
    try:
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
            f.write(current_date)
    except Exception as e:
        print(f"Warning: Could not update last run file: {e}")

def main():
    print(f"--- Bot Started at {datetime.datetime.now()} ---")

    if has_run_today():
        print("Already run today. Exiting.")
        return
    
    # Check keys
    pplx_key = os.getenv("PERPLEXITY_API_KEY")
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    discord_channel = os.getenv("DISCORD_CHANNEL_ID")
    
    if not pplx_key:
        print("Error: PERPLEXITY_API_KEY is missing.")
        return

    # Initialize agents
    client = PerplexityClient(api_key=pplx_key)
    notifier = DiscordNotifier(token=discord_token, channel_id=discord_channel)
    history = TrendHistory()  # 履歴管理（7日間保持）

    # 1. Search for Trends
    print("Searching for Alpha trends...")
    
    # Load config
    config = load_config()
    category = config.get("search_category", "Dev Tools")
    targets = config.get("target_languages", "")
    
    print(f"Category: {category}")
    print(f"Targets: {targets}")
    
    result = client.get_daily_trends(category=category, target_languages=targets)
    
    if "error" in result:
        error_detail = result['error']
        print(f"API Error: {error_detail}")
        # Discord通知用にメッセージを500文字に制限
        short_msg = error_detail[:500] if len(error_detail) > 500 else error_detail
        notifier.send(content=f"⚠️ Trend Bot Error: {short_msg}")
        return

    # 2. Filter Duplicates
    print("Checking for duplicates...")
    trends = result.get("trends", [])
    if not trends:
        print("No trends found.")
        return

    # 重複排除: 過去7日間に通知済みのツールを除外
    new_trends = [t for t in trends if not history.is_duplicate(t['name'])]
    
    if not new_trends:
        print("All trends are duplicates. Skipping notification.")
        return
    
    print(f"Found {len(new_trends)} new trend(s) out of {len(trends)}.")

    # 3. Format Message (Discord Embed)
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    summary = result.get('one_line_summary', 'No summary provided.')
    
    # Create Embed Structure
    embed = {
        "title": f"🚀 今日のテックトレンド ({date_str})",
        "description": summary,
        "color": 3066993, # Python Blue (or keep Teal)
        "fields": [],
        "footer": {
            "text": "Powered by Perplexity Sonar Pro"
        }
    }

    for i, item in enumerate(new_trends, 1):
        field_value = f"{item['description']}\n**話題性:** {item['buzz_factor']}\n[リンク]({item['url']})"
        embed["fields"].append({
            "name": f"{i}. {item['name']}",
            "value": field_value,
            "inline": False
        })
    
    # 4. Notify
    print("Sending notification...")
    if discord_token and discord_channel:
        success = notifier.send(embeds=[embed])
        if success:
            print("Notification sent successfully!")
            # 5. 通知成功後、履歴に追加
            for t in new_trends:
                history.add(t['name'], t.get('url', ''))
            print(f"Added {len(new_trends)} trend(s) to history.")
            mark_as_run_today()
        else:
            print("Failed to send notification.")
    else:
        print("No Discord credentials set. Printing to console:")
        print(f"Title: {embed['title']}")
        print(f"Summary: {embed['description']}")
        for f in embed['fields']:
            print(f"- {f['name']}: {f['value']}")
        # コンソール出力時も履歴に追加
        for t in new_trends:
            history.add(t['name'], t.get('url', ''))
        print(f"Added {len(new_trends)} trend(s) to history.")
        mark_as_run_today()

if __name__ == "__main__":
    main()
