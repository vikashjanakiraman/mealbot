from app.schemas.schemas import UserProfile, MealPlanResponse

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