import os
import sys
from dotenv import load_dotenv
from api_client import PerplexityClient
from notifier import DiscordNotifier
import datetime

# Load environment variables
load_dotenv()

def main():
    print(f"--- Bot Started at {datetime.datetime.now()} ---")
    
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

    # 1. Search for Trends
    print("Searching for Alpha trends...")
    result = client.get_daily_trends(category="Dev Tools, PKM, Privacy Browsers, & Student Deals")
    
    if "error" in result:
        print(f"API Error: {result['error']}")
        notifier.send(content=f"⚠️ Trend Bot Error: {result['error']}")
        return

    # 2. Format Message (Discord Embed)
    print("Formatting message...")
    trends = result.get("trends", [])
    if not trends:
        print("No trends found.")
        return

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

    for i, item in enumerate(trends, 1):
        field_value = f"{item['description']}\n**話題性:** {item['buzz_factor']}\n[リンク]({item['url']})"
        embed["fields"].append({
            "name": f"{i}. {item['name']}",
            "value": field_value,
            "inline": False
        })
    
    # 3. Notify
    print("Sending notification...")
    if discord_token and discord_channel:
        success = notifier.send(embeds=[embed])
        if success:
            print("Notification sent successfully!")
        else:
            print("Failed to send notification.")
    else:
        print("No Discord credentials set. Printing to console:")
        print(f"Title: {embed['title']}")
        print(f"Summary: {embed['description']}")
        for f in embed['fields']:
            print(f"- {f['name']}: {f['value']}")

if __name__ == "__main__":
    main()
