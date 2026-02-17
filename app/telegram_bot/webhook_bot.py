"""Telegram Bot with proper state management"""
from fastapi import APIRouter, Request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import requests
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Your API URL
API_URL = "https://mealbot-85zc.onrender.com"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# VALIDATE TOKEN
if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable not set!")
    TELEGRAM_TOKEN = "placeholder"
else:
    print(f"✅ TELEGRAM_BOT_TOKEN loaded")

TELEGRAM_WEBHOOK_URL = f"{API_URL}/telegram/webhook"

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Initialize bot
bot = Bot(token=TELEGRAM_TOKEN)

# Store user conversation state
user_state: Dict[int, dict] = {}

def get_user_state(user_id: int) -> dict:
    """Get or create user state"""
    if user_id not in user_state:
        user_state[user_id] = {
            "step": None,
            "goal": None,
            "diet_type": None,
            "allergies": None,
            "meal_type": None,
            "food_name": None,
            "quantity": None,
        }
    return user_state[user_id]


# ============================================================
# HELPER FUNCTIONS
# ============================================================
async def send_message(chat_id: int, text: str, reply_markup=None):
    """Send message to user"""
    try:
        print(f"📤 Sending message to {chat_id}")
        await bot.send_message(
            chat_id=chat_id, 
            text=text, 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )
        print(f"✅ Message sent to {chat_id}")
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        logger.error(f"Error sending message: {str(e)}")


# ============================================================
# COMMAND HANDLERS
# ============================================================
async def handle_start(chat_id: int, user_id: int, first_name: str):
    """Handle /start command"""
    # Reset user state
    user_state[user_id] = {"step": None}
    
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
"""
    await send_message(chat_id, text)


async def handle_plan_start(chat_id: int, user_id: int):
    """Start /plan conversation"""
    state = get_user_state(user_id)
    state["step"] = "plan_goal"
    
    reply_keyboard = [["Weight Loss", "Muscle Gain"], ["Maintenance"]]
    await send_message(
        chat_id,
        "What's your goal?",
        ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )


async def handle_plan_goal(chat_id: int, user_id: int, goal: str):
    """Handle goal selection in /plan"""
    state = get_user_state(user_id)
    state["goal"] = goal.lower().replace(" ", "_")
    state["step"] = "plan_diet"
    
    reply_keyboard = [["Veg", "Non-Veg"], ["Vegan"]]
    await send_message(
        chat_id,
        "What's your diet type?",
        ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )


async def handle_plan_diet(chat_id: int, user_id: int, diet: str):
    """Handle diet selection in /plan"""
    state = get_user_state(user_id)
    state["diet_type"] = diet.lower()
    state["step"] = "plan_allergies"
    
    await send_message(
        chat_id,
        "Any allergies? (Type 'none' if no allergies)",
        ReplyKeyboardRemove()
    )


async def handle_plan_allergies(chat_id: int, user_id: int, allergies_text: str):
    """Handle allergies in /plan and create plan"""
    state = get_user_state(user_id)
    allergies = [] if allergies_text.lower() == "none" else [a.strip() for a in allergies_text.split(",")]
    state["allergies"] = allergies
    
    # Call API to create meal plan
    try:
        response = requests.post(
            f"{API_URL}/meal-plan",
            json={
                "name": "User",
                "age": 28,
                "weight": 75,
                "height": 180,
                "diet_type": state["diet_type"],
                "goal": state["goal"],
                "allergies": allergies,
            },
        )

        if response.status_code == 200:
            plan = response.json()
            message = f"""
✅ **Your 6-Meal Plan Created!**

🌅 **Breakfast** ({plan['breakfast_cal']} cal)
{plan['breakfast']}

🍌 **Morning Snack** ({plan['morning_snack_cal']} cal)
{plan['morning_snack']}

🍽️ **Lunch** ({plan['lunch_cal']} cal)
{plan['lunch']}

☕ **Afternoon Snack** ({plan['afternoon_snack_cal']} cal)
{plan['afternoon_snack']}

🍗 **Dinner** ({plan['dinner_cal']} cal)
{plan['dinner']}

🌙 **Evening Snack** ({plan['evening_snack_cal']} cal)
{plan['evening_snack']}

**Total: {plan['total_calories']} cal/day**

Now use /log to start logging meals!
"""
            await send_message(chat_id, message)
        else:
            await send_message(chat_id, "❌ Error creating plan. Try again.")
    
    except Exception as e:
        await send_message(chat_id, f"❌ Error: {str(e)}")
    
    # Reset state
    state["step"] = None


async def handle_log_start(chat_id: int, user_id: int):
    """Start /log conversation"""
    state = get_user_state(user_id)
    state["step"] = "log_meal_type"
    
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


async def handle_log_meal_type(chat_id: int, user_id: int, meal_type: str):
    """Handle meal type in /log"""
    state = get_user_state(user_id)
    state["meal_type"] = meal_type
    state["step"] = "log_food"
    
    await send_message(
        chat_id,
        "What food? (e.g., biryani, chicken, rice)",
        ReplyKeyboardRemove()
    )


async def handle_log_food(chat_id: int, user_id: int, food_name: str):
    """Handle food name in /log"""
    state = get_user_state(user_id)
    state["food_name"] = food_name
    state["step"] = "log_quantity"
    
    await send_message(
        chat_id,
        "How much? (e.g., 1, 200, 0.5)"
    )


async def handle_log_quantity(chat_id: int, user_id: int, quantity_text: str):
    """Handle quantity in /log"""
    state = get_user_state(user_id)
    try:
        quantity = float(quantity_text)
        state["quantity"] = quantity
        state["step"] = "log_unit"
    except ValueError:
        await send_message(chat_id, "❌ Please enter a number (e.g., 1, 0.5, 200)")
        return

    reply_keyboard = [
        ["serving", "bowl"],
        ["grams", "piece"],
        ["cup", "tbsp"],
        ["ml"],
    ]
    await send_message(
        chat_id,
        "What unit?",
        ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )


async def handle_log_unit(chat_id: int, user_id: int, unit: str):
    """Handle unit in /log and log meal"""
    state = get_user_state(user_id)
    
    # Call API to log meal
    try:
        response = requests.post(
            f"{API_URL}/log-meal",
            params={
                "user_id": user_id,
                "meal_type": state["meal_type"],
                "food_name": state["food_name"],
                "quantity": state["quantity"],
                "unit": unit,
            },
        )

        if response.status_code == 200:
            result = response.json()
            message = f"""
✅ **Meal Logged!**

🍽️ {result['food']}
📏 {result['input']}
🍴 Standard serving: {result['standard_serving']}
🔥 Calories: {result['actual_calories']} cal

📊 **Today's Progress:**
Total: {result['consumed_total']} cal
Remaining: {result['remaining']} cal

💬 {result['message']}
"""
            await send_message(chat_id, message)
        else:
            await send_message(chat_id, f"❌ Error: {response.json()['error']}")

    except Exception as e:
        await send_message(chat_id, f"❌ Error: {str(e)}")
    
    # Reset state
    state["step"] = None


# ============================================================
# WEBHOOK ENDPOINT
# ============================================================
@router.post("/webhook")
async def webhook(request: Request):
    """Receive updates from Telegram via webhook"""
    print("🔔 WEBHOOK CALLED")
    
    try:
        data = await request.json()
        update = Update.de_json(data, bot)

        if not update.message:
            return {"ok": True}

        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name or "User"
        text = update.message.text or ""

        print(f"✉️ Message from {first_name} ({user_id}): {text}")
        logger.info(f"Message from {first_name} ({user_id}): {text}")

        state = get_user_state(user_id)
        current_step = state.get("step")

        # ============================================================
        # HANDLE BASED ON CURRENT CONVERSATION STEP
        # ============================================================
        
        # If in middle of conversation, handle accordingly
        if current_step == "plan_goal":
            await handle_plan_goal(chat_id, user_id, text)
        elif current_step == "plan_diet":
            await handle_plan_diet(chat_id, user_id, text)
        elif current_step == "plan_allergies":
            await handle_plan_allergies(chat_id, user_id, text)
        elif current_step == "log_meal_type":
            await handle_log_meal_type(chat_id, user_id, text)
        elif current_step == "log_food":
            await handle_log_food(chat_id, user_id, text)
        elif current_step == "log_quantity":
            await handle_log_quantity(chat_id, user_id, text)
        elif current_step == "log_unit":
            await handle_log_unit(chat_id, user_id, text)
        
        # ============================================================
        # HANDLE COMMANDS
        # ============================================================
        elif text == "/start":
            await handle_start(chat_id, user_id, first_name)
        elif text == "/help":
            await handle_help(chat_id)
        elif text == "/plan":
            await handle_plan_start(chat_id, user_id)
        elif text == "/log":
            await handle_log_start(chat_id, user_id)
        elif text == "/status":
            # Handle status
            try:
                response = requests.get(
                    f"{API_URL}/daily-status",
                    params={"user_id": user_id},
                )
                if response.status_code == 200:
                    data_resp = response.json()
                    msg = f"📊 Progress: {data_resp['consumed_calories']}/{data_resp['target_calories']} cal ({data_resp['progress']})"
                    await send_message(chat_id, msg)
                else:
                    await send_message(chat_id, "❌ No data. Use /plan first!")
            except Exception as e:
                await send_message(chat_id, f"❌ Error: {str(e)}")
        elif text == "/suggest":
            # Handle suggest
            try:
                response = requests.get(
                    f"{API_URL}/suggest-next-meal",
                    params={"user_id": user_id},
                )
                if response.status_code == 200:
                    data_resp = response.json()
                    msg = f"💡 Try: {data_resp['suggestions'][0]['food']} ({data_resp['suggestions'][0]['calories']} cal)"
                    await send_message(chat_id, msg)
                else:
                    await send_message(chat_id, "❌ Error getting suggestions")
            except Exception as e:
                await send_message(chat_id, f"❌ Error: {str(e)}")
        else:
            await send_message(chat_id, "❓ Unknown command. Use /help!")

        return {"ok": True}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Error: {str(e)}")
        return {"ok": False, "error": str(e)}


# ============================================================
# SETUP WEBHOOK
# ============================================================
async def setup_webhook():
    """Register webhook with Telegram"""
    try:
        await bot.set_webhook(url=TELEGRAM_WEBHOOK_URL)
        print(f"✅ Webhook set")
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise