"""API routes - WITH SNACKS, QUANTITY, UNIT CONVERSION, AND USER REGISTRATION"""
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


# ============================================================
# USER REGISTRATION (NEW ENDPOINT)
# ============================================================

@router.post("/register-user")
def register_user(user: UserProfile, db: Session = Depends(get_db)):
    """
    Register a new user with their profile info.
    This is called by the Telegram bot after /start completes.
    
    Parameters:
    - id: Telegram user ID (required)
    - name: User's name (required)
    - age: User's age (required)
    - weight: Weight in kg (required)
    - height: Height in cm (required)
    - diet_type: veg, non-veg, or vegan (optional)
    - goal: weight_loss, muscle_gain, or maintenance (optional)
    
    Returns:
    - User registered with ID
    """
    try:
        print(f"\n📝 Registering user: {user.name} (ID: {user.id})")
        
        # Check if user already exists
        existing = db.query(User).filter(User.id == user.id).first()
        if existing:
            print(f"⚠️  User {user.id} already exists")
            return {
                "status": "success",
                "message": "User already exists",
                "user_id": existing.id,
                "name": existing.name
            }
        
        # Create new user
        new_user = User(
            id=user.id,
            name=user.name,
            age=user.age,
            weight=user.weight,
            height=user.height,
            diet_type=user.diet_type or "non-veg",
            goal=user.goal or "maintenance"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ User registered: {new_user.id} - {new_user.name}")
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "user_id": new_user.id,
            "name": new_user.name,
            "age": new_user.age,
            "weight": new_user.weight,
            "height": new_user.height
        }
    
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return {"status": "error", "error": str(e)}, 500


# ============================================================
# MEAL PLAN ENDPOINT
# ============================================================

@router.post("/meal-plan", response_model=MealPlanResponse)
def create_meal_plan(user: UserProfile, db: Session = Depends(get_db)):
    """Create a meal plan for user with 6 meals/day including snacks"""
    db_user = create_or_get_user(db, user)
    plan = generate_meal_plan_with_snacks(user)
    save_meal_plan(db, db_user.id, plan)
    return plan


# ============================================================
# LOG MEAL ENDPOINT
# ============================================================

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
    - user_id: User ID (Telegram ID)
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
    POST /log-meal?user_id=6794649854&meal_type=lunch&food_name=biryani&quantity=1&unit=bowl
    POST /log-meal?user_id=6794649854&meal_type=lunch&food_name=biryani&quantity=200&unit=grams
    POST /log-meal?user_id=6794649854&meal_type=breakfast&food_name=almonds&quantity=23&unit=piece
    """
    
    try:
        print(f"\n🔥 Log meal request:")
        print(f"   User ID: {user_id}")
        print(f"   Meal type: {meal_type}")
        print(f"   Food: {food_name}")
        print(f"   Quantity: {quantity} {unit}")
        
        valid, msg = validate_meal_input(user_id, meal_type, food_name)
        if not valid:
            print(f"❌ Validation error: {msg}")
            return {"status": "error", "error": msg}, 400
        
        if quantity <= 0:
            print(f"❌ Quantity error: must be > 0")
            return {"status": "error", "error": "Quantity must be greater than 0"}, 400
        
        if not unit:
            print(f"❌ Unit error: required")
            return {"status": "error", "error": "Unit is required (e.g., 'bowl', 'grams', 'cup', 'piece')"}, 400
        
        # Check if user exists
        user = db.query(User).get(user_id)
        if not user:
            print(f"❌ User not found: {user_id}")
            return {"status": "error", "error": "User not found"}, 404
        
        print(f"✅ User found: {user.name}")
        
        if prevent_duplicate_log(db, user_id, food_name):
            print(f"❌ Duplicate log detected")
            return {
                "status": "error",
                "error": f"Already logged '{food_name}' in last 5 mins"
            }, 400
        
        # Search for food
        food = fuzzy_search_food(db, food_name)
        if not food:
            print(f"❌ Food not found: {food_name}")
            return {
                "status": "error",
                "error": f"Food '{food_name}' not found in database"
            }, 404
        
        print(f"✅ Food found: {food.food_name}")
        
        # Convert quantity to serving multiplier
        serving_multiplier = convert_to_serving_multiplier(
            quantity=quantity,
            user_unit=unit.lower(),
            food_serving_size=food.serving_size,
            food_serving_unit=food.serving_unit.lower(),
            food_name=food.food_name
        )
        
        if serving_multiplier is None:
            print(f"❌ Unit conversion failed")
            return {
                "status": "error",
                "error": f"Unit '{unit}' not supported. Try: {food.serving_unit}"
            }, 400
        
        print(f"✅ Serving multiplier: {serving_multiplier}")
        
        # Calculate actual nutrition
        actual_calories = int(food.default_calories * serving_multiplier)
        actual_protein = food.protein_g * serving_multiplier if food.protein_g else 0
        actual_carbs = food.carbs_g * serving_multiplier if food.carbs_g else 0
        actual_fats = food.fats_g * serving_multiplier if food.fats_g else 0
        
        print(f"✅ Calculated:")
        print(f"   Calories: {actual_calories}")
        print(f"   Protein: {actual_protein}g")
        print(f"   Carbs: {actual_carbs}g")
        print(f"   Fats: {actual_fats}g")
        
        # Create log entry
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
        
        print(f"✅ Logged to database: ID {log.id}")
        
        # Get totals
        remaining = get_remaining_calories(db, user_id, date.today())
        consumed = get_consumed_today(db, user_id)
        target = calculate_daily_calories(user.goal)["total"]
        message = handle_meal_response(consumed, target)
        
        print(f"✅ Consumed today: {consumed} / {target}")
        print(f"✅ Remaining: {remaining}")
        
        return {
            "status": "success",
            "food": food.food_name,
            "input": f"{quantity} {unit}",
            "standard_serving": food.serving_description,
            "actual_calories": actual_calories,
            "actual_protein": round(actual_protein, 1),
            "actual_carbs": round(actual_carbs, 1),
            "actual_fats": round(actual_fats, 1),
            "meal_type": meal_type,
            "consumed_total": consumed,
            "remaining": remaining,
            "message": message
        }
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"status": "error", "error": str(e)}, 500


# ============================================================
# DAILY STATUS ENDPOINT
# ============================================================

@router.get("/daily-status")
def get_daily_status(user_id: int, date_obj: date = None, db: Session = Depends(get_db)):
    """Get today's consumption and status"""
    
    try:
        if not date_obj:
            date_obj = date.today()
        
        print(f"\n📊 Status request for user {user_id} on {date_obj}")
        
        user = db.query(User).get(user_id)
        if not user:
            print(f"❌ User not found: {user_id}")
            return {"status": "error", "error": "User not found"}, 404
        
        print(f"✅ User found: {user.name}")
        
        summary = create_or_update_daily_summary(db, user_id, date_obj)
        
        logs = db.query(FoodLog).filter(
            FoodLog.user_id == user_id,
            func.date(FoodLog.logged_at) == date_obj
        ).all()
        
        print(f"✅ Found {len(logs)} meals logged")
        
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
        print(f"❌ Exception: {str(e)}")
        return {"status": "error", "error": str(e)}, 500


# ============================================================
# SUGGEST MEAL ENDPOINT
# ============================================================

@router.get("/suggest-next-meal")
def suggest_next_meal(user_id: int, db: Session = Depends(get_db)):
    """Get smart meal suggestions for right now"""
    
    try:
        print(f"\n💡 Suggestion request for user {user_id}")
        
        user = db.query(User).get(user_id)
        if not user:
            print(f"❌ User not found: {user_id}")
            return {"status": "error", "error": "User not found"}, 404
        
        print(f"✅ User found: {user.name}")
        
        targets = calculate_daily_calories(user.goal)
        meal_type = get_current_meal_type()
        target_cal = targets[meal_type]
        
        print(f"✅ Current meal type: {meal_type} (target: {target_cal} cal)")
        
        suggestions = suggest_meals_for_type(db, meal_type, user.diet_type, target_cal)
        
        print(f"✅ Found {len(suggestions)} suggestions")
        
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
        print(f"❌ Exception: {str(e)}")
        return {"status": "error", "error": str(e)}, 500
