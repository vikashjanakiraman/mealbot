"""Telegram Bot using Webhook (FREE - no background worker needed)"""
from fastapi import APIRouter, Request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import requests
import os
import logging

logger = logging.getLogger(__name__)

# Your API URL
API_URL = "https://mealbot-852c.onrender.com"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_URL = f"{API_URL}/telegram/webhook"

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Initialize bot
bot = Bot(token=TELEGRAM_TOKEN)


# ============================================================
# HELPER FUNCTIONS
# ============================================================
async def send_message(chat_id: int, text: str, reply_markup=None):
    """Send message to user"""
    try:
        await bot.send_message(
            chat_id=chat_id, 
            text=text, 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")


# ============================================================
# COMMAND HANDLERS
# ============================================================
async def handle_start(chat_id: int, first_name: str):
    """Handle /start command"""
    text = f"""
🍽️ Welcome to MealBot, {first_name}!

I'll help you:
✅ Create personalized 6-meal plans
✅ Log your food with portions
✅ Track daily calories & macros
✅ Get smart meal suggestions

Use /help to see all commands!
"""
    await send_message(chat_id, text)


async def handle_help(chat_id: int):
    """Handle /help command"""
    text = """
📋 **Available Commands:**

🎯 /plan - Create a meal plan
📝 /log - Log a meal
📊 /status - View today's progress
💡 /suggest - Get meal suggestions
❓ /help - Show this menu

**Example:**
/plan → Follow the steps
/log breakfast biryani 1 bowl
/status → See today's calories
"""
    await send_message(chat_id, text)


async def handle_plan(chat_id: int):
    """Handle /plan command"""
    reply_keyboard = [["Weight Loss", "Muscle Gain"], ["Maintenance"]]
    await send_message(
        chat_id,
        "What's your goal?",
        ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )


async def handle_log(chat_id: int):
    """Handle /log command"""
    reply_keyboard = [
        ["breakfast", "morning_snack"],
        ["lunch", "afternoon_snack"],
        ["dinner", "evening_snack"],
    ]
    await send_message(
        chat_id,
        "Which meal?",
        ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )


async def handle_status(chat_id: int, user_id: int):
    """Handle /status command"""
    try:
        response = requests.get(
            f"{API_URL}/daily-status",
            params={"user_id": user_id},
        )

        if response.status_code == 200:
            data = response.json()
            text = f"""
📊 **Your Progress Today**

👤 {data['user']} | Goal: {data['goal']}

🎯 **Calorie Target:** {data['target_calories']} cal
✅ **Consumed:** {data['consumed_calories']} cal
⬅️ **Remaining:** {data['remaining_calories']} cal

📈 **Progress:** {data['progress']}

📋 **Meals by Type:**
🌅 Breakfast: {data['meals_by_type']['breakfast']['consumed']}/{data['meals_by_type']['breakfast']['target']} cal
🍌 Morning Snack: {data['meals_by_type']['morning_snack']['consumed']}/{data['meals_by_type']['morning_snack']['target']} cal
🍽️ Lunch: {data['meals_by_type']['lunch']['consumed']}/{data['meals_by_type']['lunch']['target']} cal
☕ Afternoon Snack: {data['meals_by_type']['afternoon_snack']['consumed']}/{data['meals_by_type']['afternoon_snack']['target']} cal
🍗 Dinner: {data['meals_by_type']['dinner']['consumed']}/{data['meals_by_type']['dinner']['target']} cal
🌙 Evening Snack: {data['meals_by_type']['evening_snack']['consumed']}/{data['meals_by_type']['evening_snack']['target']} cal

📊 **Macros:**
🥩 Protein: {data['macros']['protein_g']}g
🍞 Carbs: {data['macros']['carbs_g']}g
🥑 Fats: {data['macros']['fats_g']}g

Meals logged: {data['meals_logged']}
"""
            await send_message(chat_id, text)
        else:
            await send_message(chat_id, "❌ No data found. Use /plan to create a meal plan first!")

    except Exception as e:
        await send_message(chat_id, f"❌ Error: {str(e)}")


async def handle_suggest(chat_id: int, user_id: int):
    """Handle /suggest command"""
    try:
        response = requests.get(
            f"{API_URL}/suggest-next-meal",
            params={"user_id": user_id},
        )

        if response.status_code == 200:
            data = response.json()
            text = f"""
💡 **Smart Meal Suggestions**

⏰ **Time:** {data['meal_type'].replace('_', ' ').title()}
🎯 **Target:** {data['target_calories']} cal

🍽️ **Top Suggestions:**
"""
            for i, suggestion in enumerate(data['suggestions'], 1):
                text += f"""

{i}. **{suggestion['food']}** 
   🔥 {suggestion['calories']} cal
   🥩 {suggestion['protein_g']}g protein
   🍞 {suggestion['carbs_g']}g carbs
   🥑 {suggestion['fats_g']}g fat"""

            text += "\n\nUse /log to log a meal!"
            await send_message(chat_id, text)
        else:
            await send_message(chat_id, "❌ Error getting suggestions")

    except Exception as e:
        await send_message(chat_id, f"❌ Error: {str(e)}")


# ============================================================
# WEBHOOK ENDPOINT
# ============================================================
@router.post("/webhook")
async def webhook(request: Request):
    """Receive updates from Telegram via webhook"""
    try:
        data = await request.json()
        update = Update.de_json(data, bot)

        if not update.message:
            return {"ok": True}

        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name or "User"
        text = update.message.text or ""

        logger.info(f"Message from {first_name} ({user_id}): {text}")

        # Handle commands
        if text == "/start":
            await handle_start(chat_id, first_name)
        elif text == "/help":
            await handle_help(chat_id)
        elif text == "/plan":
            await handle_plan(chat_id)
        elif text == "/log":
            await handle_log(chat_id)
        elif text == "/status":
            await handle_status(chat_id, user_id)
        elif text == "/suggest":
            await handle_suggest(chat_id, user_id)
        else:
            await send_message(chat_id, "❓ Unknown command. Use /help to see available commands.")

        return {"ok": True}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"ok": False, "error": str(e)}


# ============================================================
# SETUP WEBHOOK
# ============================================================
async def setup_webhook():
    """Register webhook with Telegram"""
    try:
        await bot.set_webhook(url=TELEGRAM_WEBHOOK_URL)
        logger.info(f"✅ Webhook set to {TELEGRAM_WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"❌ Error setting webhook: {str(e)}")
        raise
