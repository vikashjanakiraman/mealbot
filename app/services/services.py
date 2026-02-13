from app.schemas.schemas import UserProfile, MealPlanResponse
from sqlalchemy.orm import Session
from app.models.models import User, MealPlan


def generate_basic_meal_plan(user: UserProfile) -> MealPlanResponse:
    """
    Generate a basic meal plan based on user profile
    
    IMPORTANT: Must return MealPlanResponse object, NOT a dictionary!
    """
    
    # Calculate base calories based on goal
    if user.goal == "weight_loss":

        base_calories = 1800
    elif user.goal == "muscle_gain":
        base_calories = 2500
    else:  # maintain
        base_calories = 2200
    
    # Generate meals based on diet type
    if user.diet_type == "veg":
        breakfast = "Oatmeal with fruits and seeds (400 cal)"
        lunch = "Vegetable curry with brown rice and dal (600 cal)"
        dinner = "Paneer tikka with quinoa and salad (500 cal)"
    elif user.diet_type == "vegan":
        breakfast = "Smoothie bowl with chia seeds and berries (350 cal)"
        lunch = "Chickpea salad with hummus and whole grain bread (550 cal)"
        dinner = "Tofu stir-fry with vegetables and brown rice (480 cal)"
    else:  # non-veg
        breakfast = "Egg white omelette with whole wheat toast (380 cal)"
        lunch = "Grilled chicken with quinoa and veggies (650 cal)"
        dinner = "Baked fish with sweet potato and broccoli (520 cal)"
    
    # Handle allergies
    if user.allergies:
        allergies_lower = [a.lower() for a in user.allergies]
        if "nuts" in allergies_lower:
            breakfast = breakfast.replace("nuts", "seeds")
        if "dairy" in allergies_lower or "paneer" in allergies_lower:
            lunch = lunch.replace("paneer", "tofu")
    
    # CRITICAL FIX: Return MealPlanResponse object, NOT dict
    return MealPlanResponse(
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        total_calories=base_calories
    )



def create_or_get_user(db: Session, user_data):
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
        phone_number=user_data.phone_number
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
  


def save_meal_plan(db: Session, user_id: int, plan):
    db_meal = MealPlan(
        user_id=user_id,
        breakfast=plan.breakfast,
        lunch=plan.lunch,
        dinner=plan.dinner,
        total_calories=plan.total_calories
    )

    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)

    return db_meal
