def generate_basic_meal_plan(user):
    if user.diet_type == "veg":
        return {
            "breakfast": "Oats with fruits and nuts",
            "lunch": "Brown rice, dal, paneer sabzi",
            "dinner": "Chapati with mixed vegetable curry",
            "total_calories": 1800
        }
    else:
        return {
            "breakfast": "Egg omelette with toast",
            "lunch": "Grilled chicken with rice",
            "dinner": "Fish curry with vegetables",
            "total_calories": 2000
        }
