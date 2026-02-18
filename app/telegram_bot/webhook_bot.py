"""Telegram Bot (COMPLETE - Captures User Profile and Registers in Database)"""

from fastapi import APIRouter, Request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import httpx
import os
import logging
import json

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "https://mealbot-85zc.onrender.com")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    TELEGRAM_TOKEN = "placeholder"
else:
    print("✅ TELEGRAM_BOT_TOKEN loaded")

TELEGRAM_WEBHOOK_URL = f"{API_URL}/telegram/webhook"

router = APIRouter(prefix="/telegram", tags=["telegram"])
bot = Bot(token=TELEGRAM_TOKEN)

# State storage
user_state = {}
user_data = {}  # Store user profile data


def get_user_state(user_id: int) -> dict:
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


def get_user_data(user_id: int) -> dict:
    """Get stored user data (name, age, weight, height)"""
    if user_id not in user_data:
        user_data[user_id] = {
            "name": None,
            "age": None,
            "weight": None,
            "height": None,
        }
    return user_data[user_id]


def set_user_step(user_id: int, step: str):
    state = get_user_state(user_id)
    state["step"] = step
    print(f"🔄 User {user_id} step → {step}")


async def send_message(chat_id: int, text: str, reply_markup=None):
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        print(f"✅ Message sent to {chat_id}")
    except Exception as e:
        print(f"❌ Send error: {str(e)}")


def safe_get_response(response_data):
    """Handle both dict and list responses gracefully"""
    if isinstance(response_data, list):
        if len(response_data) > 0:
            return response_data[0]
        return None
    if isinstance(response_data, dict):
        return response_data
    return None


# ============================================================
# WEBHOOK
# ============================================================

@router.post("/webhook")
async def webhook(request: Request):
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

        print(f"📨 {first_name} ({user_id}): {text}")

        state = get_user_state(user_id)
        user = get_user_data(user_id)
        step = state.get("step")

        # ============================================================
        # /START - USER PROFILE CAPTURE
        # ============================================================

        if text == "/start":
            set_user_step(user_id, None)
            
            # Check if user already has profile
            if user["name"]:
                await send_message(
                    chat_id,
                    f"🍽️ Welcome back, {user['name']}!\n\nReady to plan or log meals?\n\nUse /help for commands!"
                )
            else:
                # Start profile capture
                set_user_step(user_id, "start_name")
                await send_message(
                    chat_id,
                    f"🍽️ Welcome {first_name}!\n\nLet's set up your profile!\n\n👤 What's your name?"
                )
            return {"ok": True}

        # Profile capture steps
        elif step == "start_name":
            user["name"] = text
            set_user_step(user_id, "start_age")
            await send_message(chat_id, "📅 How old are you? (15-100)")
            return {"ok": True}

        elif step == "start_age":
            try:
                age = int(text)
                if 15 <= age <= 100:
                    user["age"] = age
                    set_user_step(user_id, "start_weight")
                    await send_message(chat_id, "⚖️ Weight (in kg)? (30-300)")
                else:
                    await send_message(chat_id, "❌ Age should be 15-100")
            except ValueError:
                await send_message(chat_id, "❌ Please enter a number")
            return {"ok": True}

        elif step == "start_weight":
            try:
                weight = float(text)
                if 30 <= weight <= 300:
                    user["weight"] = weight
                    set_user_step(user_id, "start_height")
                    await send_message(chat_id, "📏 Height (in cm)? (100-250)")
                else:
                    await send_message(chat_id, "❌ Weight should be 30-300 kg")
            except ValueError:
                await send_message(chat_id, "❌ Please enter a number")
            return {"ok": True}

        elif step == "start_height":
            try:
                height = float(text)
                if 100 <= height <= 250:
                    user["height"] = height
                    set_user_step(user_id, None)
                    
                    print(f"✅ Profile captured for user {user_id}:")
                    print(f"   Name: {user['name']}")
                    print(f"   Age: {user['age']}")
                    print(f"   Weight: {user['weight']} kg")
                    print(f"   Height: {user['height']} cm")
                    
                    # ✅ NOW REGISTER USER IN DATABASE
                    async with httpx.AsyncClient() as client:
                        try:
                            print(f"📡 Calling /register-user API...")
                            resp = await client.post(
                                f"{API_URL}/register-user",
                                json={
                                    "id": user_id,
                                    "name": user["name"],
                                    "age": user["age"],
                                    "weight": user["weight"],
                                    "height": user["height"]
                                },
                                timeout=30
                            )
                            
                            if resp.status_code == 200:
                                result = resp.json()
                                print(f"✅ User registered: {result}")
                                await send_message(
                                    chat_id,
                                    f"✅ Profile saved!\n\n{user['name']}, you're all set!\n\nNow use /plan to create your meal plan! 🎯"
                                )
                            else:
                                print(f"❌ Registration failed: {resp.status_code}")
                                print(f"   Response: {resp.text}")
                                await send_message(
                                    chat_id,
                                    f"⚠️ Profile captured but registration failed. Please try /plan directly."
                                )
                        except Exception as e:
                            print(f"❌ Registration error: {e}")
                            await send_message(
                                chat_id,
                                f"⚠️ Profile captured but registration failed. Please try /plan directly."
                            )
                else:
                    await send_message(chat_id, "❌ Height should be 100-250 cm")
            except ValueError:
                await send_message(chat_id, "❌ Please enter a number")
            return {"ok": True}

        # ============================================================
        # ROOT COMMANDS
        # ============================================================

        elif text == "/help":
            await send_message(
                chat_id,
                """📋 **Commands:**

🎯 /plan - Create meal plan
📝 /log - Log a meal
📊 /status - View today's progress
💡 /suggest - Get suggestions

Use /plan to get started!"""
            )
            return {"ok": True}

        # Check if user has profile before proceeding
        if not user["name"]:
            await send_message(chat_id, "⚠️ Please use /start first to set up your profile!")
            return {"ok": True}

        # ============================================================
        # PLAN FLOW
        # ============================================================

        if text == "/plan":
            set_user_step(user_id, "plan_goal")
            reply_keyboard = [["Weight Loss", "Muscle Gain"], ["Maintenance"]]
            await send_message(
                chat_id,
                "🎯 What's your goal?",
                ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
            return {"ok": True}

        elif step == "plan_goal":
            state["goal"] = text.lower().replace(" ", "_")
            set_user_step(user_id, "plan_diet")
            reply_keyboard = [["Veg", "Non-Veg"], ["Vegan"]]
            await send_message(
                chat_id,
                "🥗 Diet type?",
                ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
            return {"ok": True}

        elif step == "plan_diet":
            state["diet_type"] = text.lower()
            set_user_step(user_id, "plan_allergies")
            await send_message(
                chat_id,
                "🚫 Any allergies? (Type 'none' if not)",
                ReplyKeyboardRemove()
            )
            return {"ok": True}

        elif step == "plan_allergies":
            allergies = [] if text.lower() == "none" else [a.strip() for a in text.split(",")]
            state["allergies"] = allergies

            # Call API with REAL user data (NOT hardcoded!)
            async with httpx.AsyncClient() as client:
                try:
                    print(f"\n📡 Calling /meal-plan API with real user data:")
                    print(f"   Name: {user['name']}")
                    print(f"   Age: {user['age']}")
                    print(f"   Weight: {user['weight']}")
                    print(f"   Height: {user['height']}")
                    
                    resp = await client.post(
                        f"{API_URL}/meal-plan",
                        json={
                            "id": user_id,
                            "name": user["name"],        # ✅ REAL DATA
                            "age": user["age"],          # ✅ REAL DATA
                            "weight": user["weight"],    # ✅ REAL DATA
                            "height": user["height"],    # ✅ REAL DATA
                            "diet_type": state["diet_type"],
                            "goal": state["goal"],
                            "allergies": allergies,
                        },
                        timeout=30
                    )

                    if resp.status_code == 200:
                        plan_data = resp.json()
                        plan = safe_get_response(plan_data)
                        
                        if plan:
                            message = f"""
✅ **Your 6-Meal Plan!**

🌅 **Breakfast** ({plan.get('breakfast_cal', '?')} cal)
{plan.get('breakfast', 'N/A')}

🍌 **Morning Snack** ({plan.get('morning_snack_cal', '?')} cal)
{plan.get('morning_snack', 'N/A')}

🍽️ **Lunch** ({plan.get('lunch_cal', '?')} cal)
{plan.get('lunch', 'N/A')}

☕ **Afternoon Snack** ({plan.get('afternoon_snack_cal', '?')} cal)
{plan.get('afternoon_snack', 'N/A')}

🍗 **Dinner** ({plan.get('dinner_cal', '?')} cal)
{plan.get('dinner', 'N/A')}

🌙 **Evening Snack** ({plan.get('evening_snack_cal', '?')} cal)
{plan.get('evening_snack', 'N/A')}

**Total: {plan.get('total_calories', '?')} cal/day**

Use /log to start logging! 📝"""
                            await send_message(chat_id, message)
                        else:
                            await send_message(chat_id, f"❌ Invalid response from API")
                    else:
                        await send_message(chat_id, f"❌ API Error {resp.status_code}")
                        
                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
                    await send_message(chat_id, f"❌ Error: {str(e)}")

            set_user_step(user_id, None)
            return {"ok": True}

        # ============================================================
        # LOG FLOW
        # ============================================================

        elif text == "/log":
            set_user_step(user_id, "log_meal_type")
            reply_keyboard = [
                ["breakfast", "morning_snack"],
                ["lunch", "afternoon_snack"],
                ["dinner", "evening_snack"]
            ]
            await send_message(
                chat_id,
                "🍽️ Which meal?",
                ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
            return {"ok": True}

        elif step == "log_meal_type":
            state["meal_type"] = text
            set_user_step(user_id, "log_food")
            await send_message(
                chat_id,
                "🥘 What food? (e.g., biryani, poha, rice)",
                ReplyKeyboardRemove()
            )
            return {"ok": True}

        elif step == "log_food":
            state["food_name"] = text
            set_user_step(user_id, "log_quantity")
            await send_message(chat_id, "📏 How much? (e.g., 1, 200, 0.5)")
            return {"ok": True}

        elif step == "log_quantity":
            try:
                state["quantity"] = float(text)
                set_user_step(user_id, "log_unit")
                reply_keyboard = [
                    ["serving", "bowl"],
                    ["grams", "piece"],
                    ["cup", "tbsp"],
                    ["ml"]
                ]
                await send_message(
                    chat_id,
                    "📐 Select unit:",
                    ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                )
            except ValueError:
                await send_message(chat_id, "❌ Please enter a number (e.g., 1, 200, 0.5)")
            return {"ok": True}

        elif step == "log_unit":
            print(f"\n🔥 Logging meal for user {user_id}")
            print(f"   Meal: {state['meal_type']} - {state['food_name']} - {state['quantity']} {text}")
            
            async with httpx.AsyncClient() as client:
                try:
                    print(f"📡 Calling /log-meal API")
                    
                    resp = await client.post(
                        f"{API_URL}/log-meal",
                        params={
                            "user_id": user_id,
                            "meal_type": state["meal_type"],
                            "food_name": state["food_name"],
                            "quantity": state["quantity"],
                            "unit": text,
                        },
                        timeout=30
                    )

                    print(f"Status: {resp.status_code}")
                    
                    if resp.status_code == 200:
                        log_data = resp.json()
                        result = safe_get_response(log_data)
                        
                        if result and isinstance(result, dict):
                            message = f"""
✅ **Meal Logged!**

🍽️ {result.get('food', 'Food')}
📏 {result.get('input', '?')}
🍴 Serving: {result.get('standard_serving', '?')}
🔥 Calories: {result.get('actual_calories', '?')} cal

📊 **Today's Progress:**
Total: {result.get('consumed_total', '?')} cal
Remaining: {result.get('remaining', '?')} cal

{result.get('message', '')}"""
                            await send_message(chat_id, message)
                            print(f"✅ Meal logged successfully!")
                        else:
                            await send_message(chat_id, f"❌ Invalid response format")
                            print(f"❌ Response: {log_data}")
                    else:
                        await send_message(chat_id, f"❌ API Error {resp.status_code}: {resp.text[:100]}")
                        
                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
                    await send_message(chat_id, f"❌ Error: {str(e)}")

            set_user_step(user_id, None)
            return {"ok": True}

        # ============================================================
        # STATUS
        # ============================================================

        elif text == "/status":
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.get(
                        f"{API_URL}/daily-status",
                        params={"user_id": user_id},
                        timeout=30
                    )

                    if resp.status_code == 200:
                        data_resp = resp.json()
                        data = safe_get_response(data_resp)
                        
                        if data:
                            message = f"""
📊 **Your Progress Today**

👤 {data.get('user', 'User')} | Goal: {data.get('goal', '?')}

🎯 **Calorie Target:** {data.get('target_calories', '?')} cal
✅ **Consumed:** {data.get('consumed_calories', '?')} cal
⬅️ **Remaining:** {data.get('remaining_calories', '?')} cal

📈 **Progress:** {data.get('progress', '?')}

📋 **Meals by Type:**
🌅 Breakfast: {data.get('meals_by_type', {}).get('breakfast', {}).get('consumed', '?')}/{data.get('meals_by_type', {}).get('breakfast', {}).get('target', '?')} cal
🍌 Morning Snack: {data.get('meals_by_type', {}).get('morning_snack', {}).get('consumed', '?')}/{data.get('meals_by_type', {}).get('morning_snack', {}).get('target', '?')} cal
🍽️ Lunch: {data.get('meals_by_type', {}).get('lunch', {}).get('consumed', '?')}/{data.get('meals_by_type', {}).get('lunch', {}).get('target', '?')} cal
☕ Afternoon Snack: {data.get('meals_by_type', {}).get('afternoon_snack', {}).get('consumed', '?')}/{data.get('meals_by_type', {}).get('afternoon_snack', {}).get('target', '?')} cal
🍗 Dinner: {data.get('meals_by_type', {}).get('dinner', {}).get('consumed', '?')}/{data.get('meals_by_type', {}).get('dinner', {}).get('target', '?')} cal
🌙 Evening Snack: {data.get('meals_by_type', {}).get('evening_snack', {}).get('consumed', '?')}/{data.get('meals_by_type', {}).get('evening_snack', {}).get('target', '?')} cal

📊 **Macros:**
🥩 Protein: {data.get('macros', {}).get('protein_g', '?')}g
🍞 Carbs: {data.get('macros', {}).get('carbs_g', '?')}g
🥑 Fats: {data.get('macros', {}).get('fats_g', '?')}g

Meals logged: {data.get('meals_logged', '?')}"""
                            await send_message(chat_id, message)
                        else:
                            await send_message(chat_id, "❌ No data. Use /plan first!")
                    else:
                        await send_message(chat_id, "❌ No data. Use /plan first!")
                except Exception as e:
                    await send_message(chat_id, f"❌ Error: {str(e)}")
            return {"ok": True}

        elif text == "/suggest":
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.get(
                        f"{API_URL}/suggest-next-meal",
                        params={"user_id": user_id},
                        timeout=30
                    )

                    if resp.status_code == 200:
                        data_resp = resp.json()
                        data = safe_get_response(data_resp)
                        
                        if data:
                            suggestions = "\n".join(
                                [f"{i}. **{s.get('food', '?')}** - {s.get('calories', '?')} cal"
                                 for i, s in enumerate(data.get("suggestions", [])[:5], 1)]
                            )
                            message = f"""
💡 **Smart Suggestions**

⏰ {data.get('meal_type', '?').replace('_', ' ').title()}
🎯 Target: {data.get('target_calories', '?')} cal

🍽️ **Top Picks:**
{suggestions}"""
                            await send_message(chat_id, message)
                        else:
                            await send_message(chat_id, "❌ Error getting suggestions")
                    else:
                        await send_message(chat_id, "❌ Error getting suggestions")
                except Exception as e:
                    await send_message(chat_id, f"❌ Error: {str(e)}")
            return {"ok": True}

        # ============================================================
        # UNKNOWN
        # ============================================================

        else:
            await send_message(chat_id, "❓ Unknown command. Use /help!")
            return {"ok": True}

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        logger.error(f"Webhook error: {str(e)}")
        return {"ok": False}


# ============================================================
# SETUP
# ============================================================

async def setup_webhook():
    try:
        await bot.set_webhook(url=TELEGRAM_WEBHOOK_URL)
        print("✅ Webhook registered")
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise
