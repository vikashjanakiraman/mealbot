"""Telegram Bot for MealBot"""
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import requests
import os
from datetime import date

# Your API URL (from Render)
API_URL = "https://mealbot-852c.onrender.com"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Conversation states
PLAN_GOAL, PLAN_DIET, PLAN_ALLERGIES = range(3)
LOG_MEAL_TYPE, LOG_FOOD, LOG_QUANTITY, LOG_UNIT = range(4)


# ============================================================
# START COMMAND
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the bot"""
    user = update.effective_user
    reply_text = f"""
🍽️ Welcome to MealBot, {user.first_name}!

I'll help you:
✅ Create personalized 6-meal plans
✅ Log your food with portions
✅ Track daily calories & macros
✅ Get smart meal suggestions

Use /help to see all commands!
"""
    await update.message.reply_text(reply_text)


# ============================================================
# HELP COMMAND
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help menu"""
    help_text = """
📋 **Available Commands:**

🎯 /plan - Create a meal plan
📝 /log - Log a meal
📊 /status - View today's progress
💡 /suggest - Get meal suggestions
❓ /help - Show this menu

**Example Usage:**
/plan → Follow the form
/log breakfast biryani 1 bowl
/status → See calories today
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


# ============================================================
# PLAN COMMAND (Conversation)
# ============================================================
async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start meal plan creation"""
    reply_keyboard = [["Weight Loss", "Muscle Gain"], ["Maintenance"]]
    await update.message.reply_text(
        "What's your goal?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return PLAN_GOAL


async def plan_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle goal selection"""
    goal = update.message.text.lower().replace(" ", "_")
    context.user_data["goal"] = goal

    reply_keyboard = [["Veg", "Non-Veg"], ["Vegan"]]
    await update.message.reply_text(
        "What's your diet type?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return PLAN_DIET


async def plan_diet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle diet selection"""
    diet = update.message.text.lower()
    context.user_data["diet_type"] = diet

    await update.message.reply_text(
        "Any allergies? (Type 'none' if no allergies)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return PLAN_ALLERGIES


async def plan_allergies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle allergies and create plan"""
    allergies_text = update.message.text
    allergies = (
        [] if allergies_text.lower() == "none" else [a.strip() for a in allergies_text.split(",")]
    )

    # Call your API
    try:
        response = requests.post(
            f"{API_URL}/meal-plan",
            json={
                "name": update.effective_user.first_name,
                "age": 28,  # Default, you could ask
                "weight": 75,  # Default, you could ask
                "height": 180,  # Default, you could ask
                "diet_type": context.user_data["diet_type"],
                "goal": context.user_data["goal"],
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
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Error creating plan. Try again.")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    return ConversationHandler.END


# ============================================================
# LOG COMMAND (Conversation)
# ============================================================
async def log_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start meal logging"""
    user_id = update.effective_user.id
    context.user_data["user_id"] = user_id

    reply_keyboard = [
        ["breakfast", "morning_snack"],
        ["lunch", "afternoon_snack"],
        ["dinner", "evening_snack"],
    ]
    await update.message.reply_text(
        "Which meal?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return LOG_MEAL_TYPE


async def log_meal_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle meal type"""
    context.user_data["meal_type"] = update.message.text

    await update.message.reply_text(
        "What food? (e.g., biryani, chicken, rice)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return LOG_FOOD


async def log_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle food name"""
    context.user_data["food_name"] = update.message.text

    await update.message.reply_text("How much? (e.g., 1, 200, 0.5)")
    return LOG_QUANTITY


async def log_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity"""
    try:
        quantity = float(update.message.text)
        context.user_data["quantity"] = quantity
    except ValueError:
        await update.message.reply_text("❌ Please enter a number (e.g., 1, 0.5, 200)")
        return LOG_QUANTITY

    reply_keyboard = [
        ["serving", "bowl"],
        ["grams", "piece"],
        ["cup", "tbsp"],
        ["ml"],
    ]
    await update.message.reply_text(
        "What unit?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return LOG_UNIT


async def log_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle unit and log meal"""
    unit = update.message.text

    # Call your API
    try:
        response = requests.post(
            f"{API_URL}/log-meal",
            params={
                "user_id": context.user_data["user_id"],
                "meal_type": context.user_data["meal_type"],
                "food_name": context.user_data["food_name"],
                "quantity": context.user_data["quantity"],
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
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Error: {response.json()['error']}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    return ConversationHandler.END


# ============================================================
# STATUS COMMAND
# ============================================================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show daily status"""
    user_id = update.effective_user.id

    try:
        response = requests.get(
            f"{API_URL}/daily-status",
            params={"user_id": user_id},
        )

        if response.status_code == 200:
            data = response.json()
            message = f"""
📊 **Your Progress Today**

👤 {data['user']} | Goal: {data['goal']}

🎯 **Calorie Target:** {data['target_calories']} cal
✅ **Consumed:** {data['consumed_calories']} cal
⬅️ **Remaining:** {data['remaining_calories']} cal

📈 **Progress:** {data['progress']}

📋 **By Meal Type:**
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
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No data found. Use /plan to create a meal plan first!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# ============================================================
# SUGGEST COMMAND
# ============================================================
async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get meal suggestions"""
    user_id = update.effective_user.id

    try:
        response = requests.get(
            f"{API_URL}/suggest-next-meal",
            params={"user_id": user_id},
        )

        if response.status_code == 200:
            data = response.json()
            message = f"""
💡 **Smart Meal Suggestions**

⏰ **Time:** {data['meal_type'].replace('_', ' ').title()}
🎯 **Target:** {data['target_calories']} cal

🍽️ **Top Suggestions:**
"""
            for i, suggestion in enumerate(data['suggestions'], 1):
                message += f"""

{i}. **{suggestion['food']}** 
   🔥 {suggestion['calories']} cal
   🥩 {suggestion['protein_g']}g protein
   🍞 {suggestion['carbs_g']}g carbs
   🥑 {suggestion['fats_g']}g fat"""

            message += "\n\nUse /log to log a meal!"
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Error getting suggestions")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# ============================================================
# CANCEL COMMAND
# ============================================================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    await update.message.reply_text(
        "Cancelled! Use /plan, /log, /status, /suggest, or /help",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ============================================================
# MAIN BOT SETUP
# ============================================================
def main() -> None:
    """Start the bot"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("suggest", suggest))

    # Plan conversation
    plan_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("plan", plan_start)],
        states={
            PLAN_GOAL: [MessageHandler(filters.TEXT, plan_goal)],
            PLAN_DIET: [MessageHandler(filters.TEXT, plan_diet)],
            PLAN_ALLERGIES: [MessageHandler(filters.TEXT, plan_allergies)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(plan_conv_handler)

    # Log conversation
    log_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("log", log_start)],
        states={
            LOG_MEAL_TYPE: [MessageHandler(filters.TEXT, log_meal_type)],
            LOG_FOOD: [MessageHandler(filters.TEXT, log_food)],
            LOG_QUANTITY: [MessageHandler(filters.TEXT, log_quantity)],
            LOG_UNIT: [MessageHandler(filters.TEXT, log_unit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(log_conv_handler)

    # Start bot
    print("✅ Bot is running!")
    app.run_polling()


if __name__ == "__main__":
    main()