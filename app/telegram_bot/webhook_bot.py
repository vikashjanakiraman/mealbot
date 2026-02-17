"""Telegram Bot with proper state management - IMPROVED"""
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
        print(f"🎯 Creating meal plan for user {user_id}")
        print(f"   Goal: {state['goal']}, Diet: {state['diet_type']}, Allergies: {allergies}")
        
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

        print(f"📥 API Response: {response.status_code}")
        
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
            error_msg = f"❌ Error creating plan. Status: {response.status_code}"
            print(f"   Error: {error_msg}")
            await send_message(chat_id, error_msg)
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"   Exception: {error_msg}")
        await send_message(chat_id, error_msg)
    
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
    
    print(f"🍽️ Meal type selected: {meal_type}")
    
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
    
    print(f"🥘 Food selected: {food_name}")
    
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
        
        print(f"📏 Quantity: {quantity}")
        
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
    except ValueError:
        print(f"❌ Invalid quantity: {quantity_text}")
        await send_message(chat_id, "❌ Please enter a number (e.g., 1, 0.5, 200)")
        return


async def handle_log_unit(chat_id: int, user_id: int, unit: str):
    """Handle unit in /log and log meal"""
    print(f"\n{'='*60}")
    print(f"🔥 LOGGING MEAL FOR USER {user_id}")
    print(f"{'='*60}")
    
    state = get_user_state(user_id)
    
    print(f"📋 State: {state}")
    print(f"🔹 User ID: {user_id}")
    print(f"🔹 Meal Type: {state['meal_type']}")
    print(f"🔹 Food Name: {state['food_name']}")
    print(f"🔹 Quantity: {state['quantity']}")
    print(f"🔹 Unit: {unit}")
    
    # Call API to log meal
    try:
        print(f"\n📡 Calling API: {API_URL}/log-meal")
        
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

        print(f"📥 API Response Status: {response.status_code}")
        print(f"📥 API Response Body: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Meal logged successfully!")
            print(f"   Food: {result.get('food')}")
            print(f"   Calories: {result.get('actual_calories')}")
            
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
            error_detail = response.json() if response.text else "No error details"
            error_msg = f"❌ Error: {error_detail}"
            print(f"❌ API Error: {error_msg}")
            await send_message(chat_id, error_msg)

    except Exception as e:
        error_msg = f"❌ Exception: {str(e)}"
        print(f"❌ {error_msg}")
        await send_message(chat_id, error_msg)
    
    finally:
        # Reset state
        print(f"🔄 Resetting state")
        state["step"] = None
        print(f"{'='*60}\n")


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
            print("⚠️ No message in update")
            return {"ok": True}

        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name or "User"
        text = update.message.text or ""

        print(f"✉️ Message from {first_name} ({user_id}): {text}")
        logger.info(f"Message from {first_name} ({user_id}): {text}")

        state = get_user_state(user_id)
        current_step = state.get("step")
        
        print(f"📍 Current step: {current_step}")

        # ============================================================
        # HANDLE BASED ON CURRENT CONVERSATION STEP
        # ============================================================
        
        # If in middle of conversation, handle accordingly
        if current_step == "plan_goal":
            print("→ Processing plan_goal")
            await handle_plan_goal(chat_id, user_id, text)
        elif current_step == "plan_diet":
            print("→ Processing plan_diet")
            await handle_plan_diet(chat_id, user_id, text)
        elif current_step == "plan_allergies":
            print("→ Processing plan_allergies")
            await handle_plan_allergies(chat_id, user_id, text)
        elif current_step == "log_meal_type":
            print("→ Processing log_meal_type")
            await handle_log_meal_type(chat_id, user_id, text)
        elif current_step == "log_food":
            print("→ Processing log_food")
            await handle_log_food(chat_id, user_id, text)
        elif current_step == "log_quantity":
            print("→ Processing log_quantity")
            await handle_log_quantity(chat_id, user_id, text)
        elif current_step == "log_unit":
            print("→ Processing log_unit")
            await handle_log_unit(chat_id, user_id, text)
        
        # ============================================================
        # HANDLE COMMANDS
        # ============================================================
        elif text == "/start":
            print("→ Processing /start")
            await handle_start(chat_id, user_id, first_name)
        elif text == "/help":
            print("→ Processing /help")
            await handle_help(chat_id)
        elif text == "/plan":
            print("→ Processing /plan")
            await handle_plan_start(chat_id, user_id)
        elif text == "/log":
            print("→ Processing /log")
            await handle_log_start(chat_id, user_id)
        elif text == "/status":
            print("→ Processing /status")
            # Handle status
            try:
                response = requests.get(
                    f"{API_URL}/daily-status",
                    params={"user_id": user_id},
                )
                if response.status_code == 200:
                    data_resp = response.json()
                    message = f"""
📊 **Your Progress Today**

👤 {data_resp['user']} | Goal: {data_resp['goal']}

🎯 **Calorie Target:** {data_resp['target_calories']} cal
✅ **Consumed:** {data_resp['consumed_calories']} cal
⬅️ **Remaining:** {data_resp['remaining_calories']} cal

📈 **Progress:** {data_resp['progress']}

📋 **Meals by Type:**
🌅 Breakfast: {data_resp['meals_by_type']['breakfast']['consumed']}/{data_resp['meals_by_type']['breakfast']['target']} cal
🍌 Morning Snack: {data_resp['meals_by_type']['morning_snack']['consumed']}/{data_resp['meals_by_type']['morning_snack']['target']} cal
🍽️ Lunch: {data_resp['meals_by_type']['lunch']['consumed']}/{data_resp['meals_by_type']['lunch']['target']} cal
☕ Afternoon Snack: {data_resp['meals_by_type']['afternoon_snack']['consumed']}/{data_resp['meals_by_type']['afternoon_snack']['target']} cal
🍗 Dinner: {data_resp['meals_by_type']['dinner']['consumed']}/{data_resp['meals_by_type']['dinner']['target']} cal
🌙 Evening Snack: {data_resp['meals_by_type']['evening_snack']['consumed']}/{data_resp['meals_by_type']['evening_snack']['target']} cal

📊 **Macros:**
🥩 Protein: {data_resp['macros']['protein_g']}g
🍞 Carbs: {data_resp['macros']['carbs_g']}g
🥑 Fats: {data_resp['macros']['fats_g']}g

Meals logged: {data_resp['meals_logged']}
"""
                    await send_message(chat_id, message)
                else:
                    await send_message(chat_id, "❌ No data. Use /plan first!")
            except Exception as e:
                await send_message(chat_id, f"❌ Error: {str(e)}")
        elif text == "/suggest":
            print("→ Processing /suggest")
            # Handle suggest
            try:
                response = requests.get(
                    f"{API_URL}/suggest-next-meal",
                    params={"user_id": user_id},
                )
                if response.status_code == 200:
                    data_resp = response.json()
                    suggestions_text = ""
                    for i, suggestion in enumerate(data_resp['suggestions'], 1):
                        suggestions_text += f"\n{i}. **{suggestion['food']}** - {suggestion['calories']} cal"
                    
                    msg = f"""
💡 **Smart Meal Suggestions**

⏰ **Time:** {data_resp['meal_type'].replace('_', ' ').title()}
🎯 **Target:** {data_resp['target_calories']} cal

🍽️ **Top Suggestions:** {suggestions_text}
"""
                    await send_message(chat_id, msg)
                else:
                    await send_message(chat_id, "❌ Error getting suggestions")
            except Exception as e:
                await send_message(chat_id, f"❌ Error: {str(e)}")
        else:
            print("→ Unknown command")
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
