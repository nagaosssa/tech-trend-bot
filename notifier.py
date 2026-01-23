import requests
import os
import json

class DiscordNotifier:
    def __init__(self, token=None, channel_id=None):
        self.token = token or os.getenv("DISCORD_BOT_TOKEN")
        self.channel_id = channel_id or os.getenv("DISCORD_CHANNEL_ID")
        self.api_base = "https://discord.com/api/v10"

    def send(self, content=None, embeds=None):
        """
        Sends a message to a Discord Channel using Bot Token.
        """
        if not self.token or not self.channel_id:
            print("Warning: DISCORD_BOT_TOKEN or DISCORD_CHANNEL_ID is not set. Notification skipped.")
            return False

        url = f"{self.api_base}/channels/{self.channel_id}/messages"
        
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

        payload = {}
        if content:
            payload["content"] = content
        if embeds:
            payload["embeds"] = embeds

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return False
