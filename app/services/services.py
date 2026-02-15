"""Services - with snacks"""
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.meal_plan import MealPlan
from app.schemas.schemas import UserProfile, MealPlanResponse


def generate_meal_plan_with_snacks(user: UserProfile) -> MealPlanResponse:
    """Generate meal plan with snacks (6 meals/day)"""
    
    # Calculate calorie split by goal
    if user.goal == "weight_loss":
        cals = {
            "breakfast": 350,
            "morning_snack": 150,
            "lunch": 500,
            "afternoon_snack": 150,
            "dinner": 500,
            "evening_snack": 150,
            "total": 1800
        }
    elif user.goal == "muscle_gain":
        cals = {
            "breakfast": 500,
            "morning_snack": 200,
            "lunch": 700,
            "afternoon_snack": 200,
            "dinner": 650,
            "evening_snack": 250,
            "total": 2500
        }
    else:  # maintain
        cals = {
            "breakfast": 400,
            "morning_snack": 150,
            "lunch": 600,
            "afternoon_snack": 150,
            "dinner": 600,
            "evening_snack": 300,
            "total": 2200
        }
    
    # Generate meals based on diet type
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
    else:  # non-veg
        meals = {
            "breakfast": f"Egg omelette + toast ({cals['breakfast']} cal)",
            "morning_snack": f"Protein shake + banana ({cals['morning_snack']} cal)",
            "lunch": f"Grilled chicken + quinoa ({cals['lunch']} cal)",
            "afternoon_snack": f"Cheese + crackers ({cals['afternoon_snack']} cal)",
            "dinner": f"Baked fish + sweet potato + broccoli ({cals['dinner']} cal)",
            "evening_snack": f"Milk + cookies ({cals['evening_snack']} cal)"
        }
    
    # Handle allergies
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