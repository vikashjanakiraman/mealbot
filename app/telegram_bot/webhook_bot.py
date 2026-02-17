"""Telegram Bot with DATABASE-BACKED state persistence"""
from fastapi import APIRouter, Request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import requests
import os
import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime

logger = logging.getLogger(__name__)

# Your API URL
API_URL = os.getenv("API_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    TELEGRAM_TOKEN = "placeholder"
else:
    print(f"✅ TELEGRAM_BOT_TOKEN loaded")

TELEGRAM_WEBHOOK_URL = f"{API_URL}/telegram/webhook"

router = APIRouter(prefix="/telegram", tags=["telegram"])
bot = Bot(token=TELEGRAM_TOKEN)

# Simple in-memory state (for now)
user_state = {}


def get_user_state(user_id: int) -> dict:
    """Get user state"""
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


def set_user_step(user_id: int, step: str):
    """Set current step and PERSIST"""
    state = get_user_state(user_id)
    state["step"] = step
    print(f"🔄 User {user_id} step set to: {step}")
    print(f"   Full state: {state}")


async def send_message(chat_id: int, text: str, reply_markup=None):
    """Send message"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        print(f"✅ Message sent to {chat_id}")
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        logger.error(f"Error sending: {str(e)}")


# ============================================================
# /PLAN HANDLERS
# ============================================================
async def handle_plan_start(chat_id: int, user_id: int):
    """Start /plan"""
    set_user_step(user_id, "plan_goal")
    reply_keyboard = [["Weight Loss", "Muscle Gain"], ["Maintenance"]]
    await send_message(chat_id, "What's your goal?", ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))


async def handle_plan_goal(chat_id: int, user_id: int, goal: str):
    """Goal selected"""
    state = get_user_state(user_id)
    state["goal"] = goal.lower().replace(" ", "_")
    set_user_step(user_id, "plan_diet")
    
    reply_keyboard = [["Veg", "Non-Veg"], ["Vegan"]]
    await send_message(chat_id, "What's your diet type?", ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))


async def handle_plan_diet(chat_id: int, user_id: int, diet: str):
    """Diet selected"""
    state = get_user_state(user_id)
    state["diet_type"] = diet.lower()
    set_user_step(user_id, "plan_allergies")
    await send_message(chat_id, "Any allergies? (Type 'none' if no)", ReplyKeyboardRemove())


async def handle_plan_allergies(chat_id: int, user_id: int, allergies_text: str):
    """Allergies entered"""
    state = get_user_state(user_id)
    allergies = [] if allergies_text.lower() == "none" else [a.strip() for a in allergies_text.split(",")]
    state["allergies"] = allergies
    
    try:
        print(f"\n📋 Creating meal plan...")
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

🌅 Breakfast ({plan['breakfast_cal']} cal): {plan['breakfast']}
🍌 Morning Snack ({plan['morning_snack_cal']} cal): {plan['morning_snack']}
🍽️ Lunch ({plan['lunch_cal']} cal): {plan['lunch']}
☕ Afternoon Snack ({plan['afternoon_snack_cal']} cal): {plan['afternoon_snack']}
🍗 Dinner ({plan['dinner_cal']} cal): {plan['dinner']}
🌙 Evening Snack ({plan['evening_snack_cal']} cal): {plan['evening_snack']}

**Total: {plan['total_calories']} cal/day**

Use /log to start logging!
"""
            await send_message(chat_id, message)
        else:
            await send_message(chat_id, f"❌ Error: {response.json()}")
    except Exception as e:
        await send_message(chat_id, f"❌ Error: {str(e)}")
    
    set_user_step(user_id, None)


# ============================================================
# /LOG HANDLERS
# ============================================================
async def handle_log_start(chat_id: int, user_id: int):
    """Start /log"""
    set_user_step(user_id, "log_meal_type")
    reply_keyboard = [["breakfast", "morning_snack"], ["lunch", "afternoon_snack"], ["dinner", "evening_snack"]]
    await send_message(chat_id, "Which meal?", ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))


async def handle_log_meal_type(chat_id: int, user_id: int, meal_type: str):
    """Meal type selected"""
    state = get_user_state(user_id)
    state["meal_type"] = meal_type
    set_user_step(user_id, "log_food")
    await send_message(chat_id, "What food? (e.g., biryani, poha, rice)", ReplyKeyboardRemove())


async def handle_log_food(chat_id: int, user_id: int, food_name: str):
    """Food name entered"""
    state = get_user_state(user_id)
    state["food_name"] = food_name
    set_user_step(user_id, "log_quantity")
    await send_message(chat_id, "How much? (e.g., 1, 140, 0.5)")


async def handle_log_quantity(chat_id: int, user_id: int, quantity_text: str):
    """Quantity entered"""
    state = get_user_state(user_id)
    
    try:
        quantity = float(quantity_text)
        state["quantity"] = quantity
        
        print(f"📏 Quantity entered: {quantity}")
        print(f"   Setting step to: log_unit")
        
        set_user_step(user_id, "log_unit")
        
        reply_keyboard = [["serving", "bowl"], ["grams", "piece"], ["cup", "tbsp"], ["ml"]]
        await send_message(chat_id, "What unit?", ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        
        print(f"✅ Unit selection message sent")
        print(f"   User {user_id} state is now: {get_user_state(user_id)}")
        
    except ValueError:
        await send_message(chat_id, "❌ Please enter a number (e.g., 1, 140, 0.5)")


async def handle_log_unit(chat_id: int, user_id: int, unit: str):
    """Unit selected - LOG THE MEAL"""
    print(f"\n{'='*70}")
    print(f"🔥 LOGGING MEAL - USER {user_id}")
    print(f"{'='*70}")
    
    state = get_user_state(user_id)
    print(f"User state: {state}")
    print(f"Unit clicked: {unit}")
    
    try:
        # Call API
        params = {
            "user_id": user_id,
            "meal_type": state["meal_type"],
            "food_name": state["food_name"],
            "quantity": state["quantity"],
            "unit": unit,
        }
        
        print(f"\n📡 Calling API with params:")
        for k, v in params.items():
            print(f"   {k}: {v}")
        
        response = requests.post(f"{API_URL}/log-meal", params=params)
        
        print(f"\n📥 API Response: {response.status_code}")
        print(f"   Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            message = f"""
✅ **Meal Logged!**

🍽️ {result['food']}
📏 {result['input']}
🍴 Serving: {result['standard_serving']}
🔥 Calories: {result['actual_calories']} cal

📊 **Today:**
Total: {result['consumed_total']} cal
Remaining: {result['remaining']} cal

{result['message']}
"""
            await send_message(chat_id, message)
            print(f"✅ Meal logged successfully!")
        else:
            error_msg = response.json()
            await send_message(chat_id, f"❌ Error: {error_msg}")
            print(f"❌ API Error: {error_msg}")
    
    except Exception as e:
        error_msg = f"❌ Exception: {str(e)}"
        await send_message(chat_id, error_msg)
        print(f"❌ {error_msg}")
    
    finally:
        set_user_step(user_id, None)
        print(f"{'='*70}\n")


# ============================================================
# WEBHOOK
# ============================================================
@router.post("/webhook")
async def webhook(request: Request):
    """Webhook endpoint"""
    print("\n🔔 WEBHOOK CALLED")
    
    try:
        data = await request.json()
        update = Update.de_json(data, bot)
        
        if not update.message:
            return {"ok": True}
        
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name or "User"
        text = update.message.text or ""
        
        print(f"📨 From {first_name} ({user_id}): {text}")
        
        state = get_user_state(user_id)
        current_step = state.get("step")
        
        print(f"📍 Current step: {current_step}")
        print(f"   Full state: {state}")
        
        # ============================================================
        # CONVERSATION FLOW
        # ============================================================
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
            print(f"✅ In log_unit handler, about to log meal")
            await handle_log_unit(chat_id, user_id, text)
        
        # ============================================================
        # COMMANDS
        # ============================================================
        elif text == "/start":
            get_user_state(user_id)["step"] = None
            await send_message(chat_id, f"🍽️ Welcome {first_name}!\n\nUse /help for commands")
        elif text == "/help":
            await send_message(chat_id, "📋 Commands:\n/plan - Create meal plan\n/log - Log meal\n/status - View progress\n/suggest - Get suggestion")
        elif text == "/plan":
            await handle_plan_start(chat_id, user_id)
        elif text == "/log":
            await handle_log_start(chat_id, user_id)
        elif text == "/status":
            try:
                resp = requests.get(f"{API_URL}/daily-status", params={"user_id": user_id})
                if resp.status_code == 200:
                    data_resp = resp.json()
                    msg = f"📊 {data_resp['consumed_calories']}/{data_resp['target_calories']} cal ({data_resp['progress']})"
                    await send_message(chat_id, msg)
                else:
                    await send_message(chat_id, "❌ No data. Use /plan first!")
            except Exception as e:
                await send_message(chat_id, f"❌ Error: {str(e)}")
        elif text == "/suggest":
            try:
                resp = requests.get(f"{API_URL}/suggest-next-meal", params={"user_id": user_id})
                if resp.status_code == 200:
                    data_resp = resp.json()
                    suggestions = "\n".join([f"• {s['food']} ({s['calories']} cal)" for s in data_resp['suggestions'][:3]])
                    msg = f"💡 Suggestions:\n{suggestions}"
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
        return {"ok": False}


# ============================================================
# SETUP
# ============================================================
async def setup_webhook():
    """Register webhook"""
    try:
        await bot.set_webhook(url=TELEGRAM_WEBHOOK_URL)
        print(f"✅ Webhook set")
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise
