"""Telegram Bot (IMPROVED – Async, Clean, Non-blocking)"""

from fastapi import APIRouter, Request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import httpx
import os
import logging

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
        step = state.get("step")

        # ============================================================
        # ROOT COMMANDS
        # ============================================================

        if text == "/start":
            set_user_step(user_id, None)
            await send_message(
                chat_id,
                f"🍽️ Welcome {first_name}!\n\nI help you:\n✅ Create meal plans\n✅ Log meals\n✅ Track calories\n\nUse /help for commands!"
            )
            return {"ok": True}

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

        # ============================================================
        # PLAN FLOW
        # ============================================================

        elif text == "/plan":
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

            # Call API to create plan
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        f"{API_URL}/meal-plan",
                        json={
                            "name": first_name,
                            "age": 28,
                            "weight": 75,
                            "height": 180,
                            "diet_type": state["diet_type"],
                            "goal": state["goal"],
                            "allergies": allergies,
                        },
                        timeout=30
                    )

                    if resp.status_code == 200:
                        plan = resp.json()
                        message = f"""
✅ **Your 6-Meal Plan!**

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

Use /log to start logging! 📝"""
                        await send_message(chat_id, message)
                    else:
                        await send_message(chat_id, f"❌ Error: {resp.text}")
                except Exception as e:
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
            # Log the meal via API
            async with httpx.AsyncClient() as client:
                try:
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

                    if resp.status_code == 200:
                        result = resp.json()
                        message = f"""
✅ **Meal Logged!**

🍽️ {result['food']}
📏 {result['input']}
🍴 Serving: {result['standard_serving']}
🔥 Calories: {result['actual_calories']} cal

📊 **Today's Progress:**
Total: {result['consumed_total']} cal
Remaining: {result['remaining']} cal

{result['message']}"""
                        await send_message(chat_id, message)
                    else:
                        error = resp.json()
                        await send_message(chat_id, f"❌ Error: {error}")
                except Exception as e:
                    await send_message(chat_id, f"❌ Error: {str(e)}")

            set_user_step(user_id, None)
            return {"ok": True}

        # ============================================================
        # STATUS & SUGGEST
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

Meals logged: {data_resp['meals_logged']}"""
                        await send_message(chat_id, message)
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
                        suggestions = "\n".join(
                            [f"{i}. **{s['food']}** - {s['calories']} cal"
                             for i, s in enumerate(data_resp["suggestions"][:5], 1)]
                        )
                        message = f"""
💡 **Smart Suggestions**

⏰ {data_resp['meal_type'].replace('_', ' ').title()}
🎯 Target: {data_resp['target_calories']} cal

🍽️ **Top Picks:**
{suggestions}"""
                        await send_message(chat_id, message)
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
