import asyncio
from telegram import Bot
from config import Config

class TelegramNotifier:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
    
    async def send_order_notification(self, order_data):
        """Send order notification to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("Telegram credentials not configured")
            return False
        
        try:
            bot = Bot(token=self.bot_token)
            
            message = "📩 *New Contact Message!*\n\n"
            message += f"*Name:* {order_data['name']}\n"
            message += f"*Email:* {order_data['email']}\n"
            
            # Extract the actual message from the address field
            if 'Contact Message:' in order_data['address']:
                actual_message = order_data['address'].replace('Contact Message:', '').strip()
                message += f"\n*Message:*\n{actual_message}"
            
            # Support both numeric chat IDs and channel usernames
            chat_id = self.chat_id
            if not chat_id.startswith('@') and not chat_id.lstrip('-').isdigit():
                chat_id = f"@{chat_id}"
            
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            return False
    
    def send_order(self, order_data):
        """Synchronous wrapper for sending order notification"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_order_notification(order_data))
            loop.close()
            return result
        except Exception as e:
            print(f"Error in sync wrapper: {e}")
            return False
