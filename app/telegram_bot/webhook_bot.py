"""Telegram Bot (FIXED – Non-blocking & Safe for Render)"""

from fastapi import APIRouter, Request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
import httpx
import os
import logging

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
    TELEGRAM_TOKEN = "placeholder"
else:
    print("✅ TELEGRAM_BOT_TOKEN loaded")

TELEGRAM_WEBHOOK_URL = f"{API_URL}/telegram/webhook"

router = APIRouter(prefix="/telegram", tags=["telegram"])
bot = Bot(token=TELEGRAM_TOKEN)

# Simple in-memory state
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
        # COMMANDS
        # ============================================================

        if text == "/start":
            set_user_step(user_id, None)
            await send_message(chat_id, f"🍽️ Welcome {first_name}!\n\nUse /help")

        elif text == "/help":
            await send_message(chat_id, "📋 Commands:\n/plan\n/log\n/status\n/suggest")

        elif text == "/status":
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/daily-status",
                    params={"user_id": user_id},
                    timeout=20
                )

            if resp.status_code == 200:
                data_resp = resp.json()
                msg = (
                    f"📊 {data_resp['consumed_calories']}/"
                    f"{data_resp['target_calories']} cal\n"
                    f"{data_resp['progress']}"
                )
                await send_message(chat_id, msg)
            else:
                await send_message(chat_id, "❌ No data yet.")

        elif text == "/suggest":
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/suggest-next-meal",
                    params={"user_id": user_id},
                    timeout=20
                )

            if resp.status_code == 200:
                data_resp = resp.json()
                suggestions = "\n".join(
                    [f"• {s['food']} ({s['calories']} cal)"
                     for s in data_resp["suggestions"][:3]]
                )
                await send_message(chat_id, f"💡 Suggestions:\n{suggestions}")
            else:
                await send_message(chat_id, "❌ Suggestion error")

        elif text == "/log":
            set_user_step(user_id, "log_food")
            await send_message(chat_id, "What food?")

        elif step == "log_food":
            state["food_name"] = text
            set_user_step(user_id, "log_quantity")
            await send_message(chat_id, "How much?")

        elif step == "log_quantity":
            try:
                state["quantity"] = float(text)
                set_user_step(user_id, "log_unit")
                reply_keyboard = [["serving", "grams"], ["bowl", "piece"]]
                await send_message(
                    chat_id,
                    "Select unit:",
                    ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                )
            except:
                await send_message(chat_id, "❌ Enter number")

        elif step == "log_unit":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/log-meal",
                    params={
                        "user_id": user_id,
                        "meal_type": "breakfast",
                        "food_name": state["food_name"],
                        "quantity": state["quantity"],
                        "unit": text,
                    },
                    timeout=20
                )

            if resp.status_code == 200:
                result = resp.json()
                await send_message(
                    chat_id,
                    f"✅ Logged {result['food']} - "
                    f"{result['actual_calories']} cal"
                )
            else:
                await send_message(chat_id, "❌ Log failed")

            set_user_step(user_id, None)

        else:
            await send_message(chat_id, "❓ Unknown command")

        return {"ok": True}

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return {"ok": False}


# ============================================================
# SETUP
# ============================================================

async def setup_webhook():
    await bot.set_webhook(url=TELEGRAM_WEBHOOK_URL)
    print("✅ Webhook registered")
