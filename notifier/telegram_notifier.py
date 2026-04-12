import requests
import logging
from typing import Dict

class TelegramNotifier:
    def __init__(self, config: Dict):
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    def send_notification(self, listing: Dict) -> bool:
        """Send Telegram notification for a new listing"""
        if not self.bot_token or not self.chat_id:
            logging.warning("Telegram bot token or chat ID not configured")
            return False
            
        try:
            message = f"""
            🏠 New Apartment Listing!
            
            *Title:* {listing['title']}
            *Price:* {listing['price']} EUR
            *District:* {listing['district']}
            *Source:* {listing['source']}
            
            [View Listing]({listing['url']})
            """
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(self.api_url, data=payload)
            
            if response.status_code == 200:
                logging.info(f"Telegram notification sent for listing: {listing['title']}")
                return True
            else:
                logging.error(f"Failed to send Telegram notification: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending Telegram notification: {e}")
            return False
