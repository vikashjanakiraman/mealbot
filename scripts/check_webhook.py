"""Check and fix Telegram webhook"""
import os
import asyncio
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = "https://mealbot-852c.onrender.com/telegram/webhook"

async def check_webhook():
    """Check webhook status"""
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # Check current webhook
    print("🔍 Checking webhook status...")
    info = await bot.get_webhook_info()
    print(f"Current webhook: {info}")
    
    # Get bot info
    print("\n🤖 Checking bot info...")
    me = await bot.get_me()
    print(f"Bot: @{me.username}")
    print(f"Bot ID: {me.id}")
    
    # Re-register webhook
    print(f"\n🔧 Re-registering webhook to: {WEBHOOK_URL}")
    result = await bot.set_webhook(url=WEBHOOK_URL)
    print(f"Result: {result}")
    
    # Check again
    print("\n✅ New webhook status:")
    info = await bot.get_webhook_info()
    print(f"URL: {info.url}")
    print(f"Has custom cert: {info.has_custom_certificate}")
    print(f"Pending updates: {info.pending_update_count}")
    print(f"Last error: {info.last_error_message}")

if __name__ == "__main__":
    asyncio.run(check_webhook())