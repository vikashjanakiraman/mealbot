"""Services - with snacks and unit conversion for accurate tracking"""
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from difflib import SequenceMatcher

from app.models.user import User
from app.models.meal_plan import MealPlan
from app.models.food_log import FoodLog
from app.models.food_database import FoodDatabase
from app.schemas.schemas import UserProfile, MealPlanResponse


def calculate_daily_calories(goal: str) -> dict:
    """Calculate calorie split by goal and meal type"""
    if goal == "weight_loss":
        return {
            "breakfast": 350,
            "morning_snack": 150,
            "lunch": 500,
            "afternoon_snack": 150,
            "dinner": 500,
            "evening_snack": 150,
            "total": 1800
        }
    elif goal == "muscle_gain":
        return {
            "breakfast": 500,
            "morning_snack": 200,
            "lunch": 700,
            "afternoon_snack": 200,
            "dinner": 650,
            "evening_snack": 250,
            "total": 2500
        }
    else:
        return {
            "breakfast": 400,
            "morning_snack": 150,
            "lunch": 600,
            "afternoon_snack": 150,
            "dinner": 600,
            "evening_snack": 300,
            "total": 2200
        }


def generate_meal_plan_with_snacks(user: UserProfile) -> MealPlanResponse:
    """Generate meal plan with snacks (6 meals/day)"""
    cals = calculate_daily_calories(user.goal)
    
    if user.diet_type == "veg":
        meals = {
            "breakfast": f"Oatmeal with berries ({cals['breakfast']} cal)",
            "morning_snack": f"Banana + almonds ({cals['morning_snack']} cal)",
            "lunch": f"Veggie curry + rice + dal ({cals['lunch']} cal)",
            "afternoon_snack": f"Greek yogurt + granola ({cals['afternoon_snack']} cal)",
            "dinner": f"Paneer tikka + quinoa + salad ({cals['dinner']} cal)",
            "evening_snack": f"Herbal tea + biscuits ({cals['evening_snack']} cal)"
        }
    elif user.diet_type == "vegan":
        meals = {
            "breakfast": f"Smoothie bowl with chia ({cals['breakfast']} cal)",
            "morning_snack": f"Apple + peanut butter ({cals['morning_snack']} cal)",
            "lunch": f"Chickpea salad + hummus bread ({cals['lunch']} cal)",
            "afternoon_snack": f"Almonds + dates ({cals['afternoon_snack']} cal)",
            "dinner": f"Tofu stir-fry + brown rice ({cals['dinner']} cal)",
            "evening_snack": f"Coconut milk tea ({cals['evening_snack']} cal)"
        }
    else:
        meals = {
            "breakfast": f"Egg omelette + toast ({cals['breakfast']} cal)",
            "morning_snack": f"Protein shake + banana ({cals['morning_snack']} cal)",
            "lunch": f"Grilled chicken + quinoa ({cals['lunch']} cal)",
            "afternoon_snack": f"Cheese + crackers ({cals['afternoon_snack']} cal)",
            "dinner": f"Baked fish + sweet potato + broccoli ({cals['dinner']} cal)",
            "evening_snack": f"Milk + cookies ({cals['evening_snack']} cal)"
        }
    
    if user.allergies:
        allergies_lower = [a.lower() for a in user.allergies]
        if "nuts" in allergies_lower:
            meals["morning_snack"] = meals["morning_snack"].replace("almonds", "seeds")
        if "dairy" in allergies_lower:
            meals["afternoon_snack"] = meals["afternoon_snack"].replace("yogurt", "coconut")
    
    return MealPlanResponse(
        breakfast=meals["breakfast"],
        breakfast_cal=cals["breakfast"],
        morning_snack=meals["morning_snack"],
        morning_snack_cal=cals["morning_snack"],
        lunch=meals["lunch"],
        lunch_cal=cals["lunch"],
        afternoon_snack=meals["afternoon_snack"],
        afternoon_snack_cal=cals["afternoon_snack"],
        dinner=meals["dinner"],
        dinner_cal=cals["dinner"],
        evening_snack=meals["evening_snack"],
        evening_snack_cal=cals["evening_snack"],
        total_calories=cals["total"]
    )


def create_or_get_user(db: Session, user_data: UserProfile) -> User:
    """Create or get user"""
    existing_user = None
    if user_data.phone_number:
        existing_user = db.query(User).filter(
            User.phone_number == user_data.phone_number
        ).first()
    
    if existing_user:
        return existing_user
    
    new_user = User(
        name=user_data.name,
        age=user_data.age,
        weight=user_data.weight,
        height=user_data.height,
        goal=user_data.goal,
        diet_type=user_data.diet_type,
        phone_number=user_data.phone_number,
        allergies=",".join(user_data.allergies) if user_data.allergies else None,
        preferences=user_data.preferences
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


def save_meal_plan(db: Session, user_id: int, plan: MealPlanResponse) -> MealPlan:
    """Save meal plan"""
    db_meal = MealPlan(
        user_id=user_id,
        breakfast=plan.breakfast,
        breakfast_cal=plan.breakfast_cal,
        morning_snack=plan.morning_snack,
        morning_snack_cal=plan.morning_snack_cal,
        lunch=plan.lunch,
        lunch_cal=plan.lunch_cal,
        afternoon_snack=plan.afternoon_snack,
        afternoon_snack_cal=plan.afternoon_snack_cal,
        dinner=plan.dinner,
        dinner_cal=plan.dinner_cal,
        evening_snack=plan.evening_snack,
        evening_snack_cal=plan.evening_snack_cal,
        total_calories=plan.total_calories
    )
    
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    
    return db_meal


def prevent_duplicate_log(db: Session, user_id: int, food_name: str, minutes: int = 5) -> bool:
    """Check if same food logged in last N minutes"""
    cutoff = datetime.now() - timedelta(minutes=minutes)
    
    existing = db.query(FoodLog).filter(
        FoodLog.user_id == user_id,
        FoodLog.food_name == food_name,
        FoodLog.logged_at > cutoff
    ).first()
    
    return existing is not None


def validate_meal_input(user_id: int, meal_type: str, food_name: str) -> tuple:
    """Validate meal log input"""
    valid_meal_types = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "evening_snack"]
    
    if not user_id or user_id <= 0:
        return False, "Invalid user ID"
    
    if meal_type not in valid_meal_types:
        return False, f"Invalid meal type. Must be one of: {', '.join(valid_meal_types)}"
    
    if not food_name or len(food_name) < 2:
        return False, "Food name must be at least 2 characters"
    
    return True, "Valid"


def fuzzy_search_food(db: Session, food_name: str):
    """Search for food by name with fuzzy matching"""
    food_name_lower = food_name.lower().strip()
    
    exact_match = db.query(FoodDatabase).filter(
        FoodDatabase.food_name.ilike(food_name_lower)
    ).first()
    
    if exact_match:
        return exact_match
    
    all_foods = db.query(FoodDatabase).all()
    for food in all_foods:
        if food.aliases:
            aliases = [a.strip().lower() for a in food.aliases.split(';')]
            if food_name_lower in aliases:
                return food
    
    best_match = None
    best_ratio = 0
    
    for food in all_foods:
        ratio = SequenceMatcher(None, food_name_lower, food.food_name.lower()).ratio()
        if ratio > best_ratio and ratio > 0.6:
            best_ratio = ratio
            best_match = food
    
    return best_match


def get_remaining_calories(db: Session, user_id: int, date_obj: date) -> int:
    """Get remaining calories for the day"""
    user = db.query(User).get(user_id)
    if not user:
        return 0
    
    targets = calculate_daily_calories(user.goal)
    consumed = db.query(func.sum(FoodLog.calories)).filter(
        FoodLog.user_id == user_id,
        func.date(FoodLog.logged_at) == date_obj
    ).scalar() or 0
    
    return targets["total"] - consumed


def get_consumed_today(db: Session, user_id: int) -> int:
    """Get total calories consumed today"""
    consumed = db.query(func.sum(FoodLog.calories)).filter(
        FoodLog.user_id == user_id,
        func.date(FoodLog.logged_at) == date.today()
    ).scalar() or 0
    
    return consumed


def handle_meal_response(consumed: int, target: int) -> str:
    """Generate helpful message"""
    remaining = target - consumed
    
    if remaining < 0:
        over_by = abs(remaining)
        if over_by <= 100:
            return f"You're {over_by} cal over. Light snack next time!"
        else:
            return f"You're {over_by} cal over. Tomorrow's a new day!"
    elif remaining > 500:
        return f"Great start! You have {remaining} cal left. Keep going!"
    elif remaining > 200:
        return f"Nice! You have {remaining} cal left. Consider a snack."
    else:
        return f"Almost there! {remaining} cal remaining."


def convert_to_serving_multiplier(quantity: float, user_unit: str, food_serving_size: int, food_serving_unit: str, food_name: str) -> float:
    """Convert user's input to serving multiplier"""
    
    if user_unit == "serving":
        return quantity
    
    if user_unit == "grams" and food_serving_unit == "grams":
        return quantity / food_serving_size
    
    if user_unit == "ml" and food_serving_unit == "ml":
        return quantity / food_serving_size
    
    if user_unit == food_serving_unit:
        return quantity / food_serving_size
    
    conversions = {
        ("cup", "grams"): {"oatmeal": 50, "rice": 200, "dal": 200},
        ("tbsp", "grams"): {"peanut_butter": 16, "honey": 20},
        ("piece", "grams"): {"almonds": 1.2, "samosa": 100, "idli": 60},
        ("bowl", "grams"): {"biryani": 400, "curry": 200, "dal": 200},
    }
    
    key = (user_unit, food_serving_unit)
    if key in conversions:
        food_lower = food_name.lower()
        for food_alias, conversion_factor in conversions[key].items():
            if food_alias in food_lower:
                return (quantity * conversion_factor) / food_serving_size
    
    return None


def suggest_meals_for_type(db: Session, meal_type: str, diet_type: str, calorie_target: int) -> list:
    """Suggest meals for a specific meal type"""
    foods = db.query(FoodDatabase).filter(
        FoodDatabase.category == meal_type
    ).all()
    
    suggestions = [
        f for f in foods 
        if calorie_target - 100 <= f.default_calories <= calorie_target + 100
    ]
    
    return suggestions[:5]


def get_current_meal_type() -> str:
    """Suggest meal type based on current time"""
    hour = datetime.now().hour
    
    if 6 <= hour < 10:
        return "breakfast"
    elif 10 <= hour < 12:
        return "morning_snack"
    elif 12 <= hour < 15:
        return "lunch"
    elif 15 <= hour < 17:
        return "afternoon_snack"
    elif 17 <= hour < 20:
        return "dinner"
    else:
        return "evening_snack"


def create_or_update_daily_summary(db: Session, user_id: int, date_obj: date):
    """Create or update daily summary for user"""
    from app.models.daily_summary import DailySummary
    
    user = db.query(User).get(user_id)
    if not user:
        return None
    
    targets = calculate_daily_calories(user.goal)
    
    summary = db.query(DailySummary).filter(
        DailySummary.user_id == user_id,
        DailySummary.date == date_obj
    ).first()
    
    logs = db.query(FoodLog).filter(
        FoodLog.user_id == user_id,
        func.date(FoodLog.logged_at) == date_obj
    ).all()
    
    consumed = sum(log.calories for log in logs)
    protein = sum(log.protein_g for log in logs)
    carbs = sum(log.carbs_g for log in logs)
    fats = sum(log.fats_g for log in logs)
    
    if summary:
        summary.consumed_calories = consumed
        summary.remaining_calories = targets["total"] - consumed
        summary.total_protein_g = protein
        summary.total_carbs_g = carbs
        summary.total_fats_g = fats
        summary.meals_logged = len(logs)
    else:
        summary = DailySummary(
            user_id=user_id,
            date=date_obj,
            target_calories=targets["total"],
            consumed_calories=consumed,
            remaining_calories=targets["total"] - consumed,
            total_protein_g=protein,
            total_carbs_g=carbs,
            total_fats_g=fats,
            meals_logged=len(logs)
        )
        db.add(summary)
    
    db.commit()
    return summary
