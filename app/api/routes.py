"""API routes - WITH SNACKS, QUANTITY, AND UNIT CONVERSION"""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.food_log import FoodLog
from app.models.food_database import FoodDatabase
from app.models.daily_summary import DailySummary

from app.schemas.schemas import UserProfile, MealPlanResponse

from app.services.services import (
    generate_meal_plan_with_snacks,
    create_or_get_user,
    save_meal_plan,
    prevent_duplicate_log,
    validate_meal_input,
    fuzzy_search_food,
    get_remaining_calories,
    get_consumed_today,
    handle_meal_response,
    calculate_daily_calories,
    suggest_meals_for_type,
    get_current_meal_type,
    create_or_update_daily_summary,
    convert_to_serving_multiplier
)

from app.database.session import get_db

router = APIRouter()


@router.post("/meal-plan", response_model=MealPlanResponse)
def create_meal_plan(user: UserProfile, db: Session = Depends(get_db)):
    """Create a meal plan for user with 6 meals/day including snacks"""
    db_user = create_or_get_user(db, user)
    plan = generate_meal_plan_with_snacks(user)
    save_meal_plan(db, db_user.id, plan)
    return plan


@router.post("/log-meal")
def log_meal(
    user_id: int, 
    meal_type: str, 
    food_name: str, 
    quantity: float,
    unit: str = "serving",
    db: Session = Depends(get_db)
):
    """
    Log a meal with explicit quantity and unit.
    
    Parameters:
    - user_id: User ID
    - meal_type: breakfast, morning_snack, lunch, afternoon_snack, dinner, evening_snack
    - food_name: Name of food
    - quantity: How much (required)
    - unit: What unit (optional, default: "serving")
      * "serving" = 1 standard serving
      * "bowl" = 1 bowl
      * "cup" = 1 cup
      * "grams" = grams
      * "piece" = piece
      * "tbsp" = tablespoon
      * "ml" = milliliter
    
    Examples:
    POST /log-meal?user_id=1&meal_type=lunch&food_name=biryani&quantity=1&unit=bowl
    POST /log-meal?user_id=1&meal_type=lunch&food_name=biryani&quantity=200&unit=grams
    POST /log-meal?user_id=1&meal_type=breakfast&food_name=almonds&quantity=23&unit=piece
    """
    
    try:
        valid, msg = validate_meal_input(user_id, meal_type, food_name)
        if not valid:
            return {"status": "error", "error": msg}, 400
        
        if quantity <= 0:
            return {"status": "error", "error": "Quantity must be greater than 0"}, 400
        
        if not unit:
            return {"status": "error", "error": "Unit is required (e.g., 'bowl', 'grams', 'cup', 'piece')"}, 400
        
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "error": "User not found"}, 404
        
        if prevent_duplicate_log(db, user_id, food_name):
            return {
                "status": "error",
                "error": f"Already logged '{food_name}' in last 5 mins"
            }, 400
        
        food = fuzzy_search_food(db, food_name)
        if not food:
            return {
                "status": "error",
                "error": f"Food '{food_name}' not found in database"
            }, 404
        
        serving_multiplier = convert_to_serving_multiplier(
            quantity=quantity,
            user_unit=unit.lower(),
            food_serving_size=food.serving_size,
            food_serving_unit=food.serving_unit.lower(),
            food_name=food.food_name
        )
        
        if serving_multiplier is None:
            return {
                "status": "error",
                "error": f"Unit '{unit}' not supported. Try: {food.serving_unit}"
            }, 400
        
        actual_calories = int(food.default_calories * serving_multiplier)
        actual_protein = food.protein_g * serving_multiplier
        actual_carbs = food.carbs_g * serving_multiplier
        actual_fats = food.fats_g * serving_multiplier
        
        log = FoodLog(
            user_id=user_id,
            meal_type=meal_type,
            food_name=food.food_name,
            calories=actual_calories,
            protein_g=actual_protein,
            carbs_g=actual_carbs,
            fats_g=actual_fats
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        remaining = get_remaining_calories(db, user_id, date.today())
        consumed = get_consumed_today(db, user_id)
        target = calculate_daily_calories(user.goal)["total"]
        message = handle_meal_response(consumed, target)
        
        return {
            "status": "success",
            "food": food.food_name,
            "input": f"{quantity} {unit}",
            "standard_serving": food.serving_description,
            "actual_calories": actual_calories,
            "meal_type": meal_type,
            "consumed_total": consumed,
            "remaining": remaining,
            "message": message
        }
    
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500


@router.get("/daily-status")
def get_daily_status(user_id: int, date_obj: date = None, db: Session = Depends(get_db)):
    """Get today's consumption and status"""
    
    try:
        if not date_obj:
            date_obj = date.today()
        
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "error": "User not found"}, 404
        
        summary = create_or_update_daily_summary(db, user_id, date_obj)
        
        logs = db.query(FoodLog).filter(
            FoodLog.user_id == user_id,
            func.date(FoodLog.logged_at) == date_obj
        ).all()
        
        by_meal_type = {}
        targets = calculate_daily_calories(user.goal)
        
        for meal_type in ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "evening_snack"]:
            meals = [l for l in logs if l.meal_type == meal_type]
            consumed = sum(m.calories for m in meals)
            
            by_meal_type[meal_type] = {
                "target": targets[meal_type],
                "consumed": consumed,
                "remaining": targets[meal_type] - consumed,
                "items": [m.food_name for m in meals]
            }
        
        return {
            "status": "success",
            "date": date_obj,
            "user": user.name,
            "goal": user.goal,
            "target_calories": summary.target_calories,
            "consumed_calories": summary.consumed_calories,
            "remaining_calories": summary.remaining_calories,
            "meals_by_type": by_meal_type,
            "meals_logged": summary.meals_logged,
            "macros": {
                "protein_g": round(summary.total_protein_g, 1),
                "carbs_g": round(summary.total_carbs_g, 1),
                "fats_g": round(summary.total_fats_g, 1)
            },
            "progress": f"{(summary.consumed_calories / summary.target_calories * 100):.0f}%"
        }
    
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500


@router.get("/suggest-next-meal")
def suggest_next_meal(user_id: int, db: Session = Depends(get_db)):
    """Get smart meal suggestions for right now"""
    
    try:
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "error": "User not found"}, 404
        
        targets = calculate_daily_calories(user.goal)
        meal_type = get_current_meal_type()
        target_cal = targets[meal_type]
        
        suggestions = suggest_meals_for_type(db, meal_type, user.diet_type, target_cal)
        
        return {
            "status": "success",
            "user": user.name,
            "meal_type": meal_type,
            "target_calories": target_cal,
            "suggestions": [
                {
                    "food": s.food_name,
                    "calories": s.default_calories,
                    "protein_g": s.protein_g,
                    "carbs_g": s.carbs_g,
                    "fats_g": s.fats_g,
                    "cuisine": s.cuisine,
                    "diet_type": s.diet_type
                }
                for s in suggestions
            ]
        }
    
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500
