from fastapi import FastAPI
from app.schemas.schemas import UserProfile, MealPlanResponse
from app.services.services import generate_basic_meal_plan

app = FastAPI(title="Smart Meal Planner API")

@app.get("/")
def health_check():
    return {"message": "Meal Planner API is running 🚀"}

@app.post("/generate-meal-plan", response_model=MealPlanResponse)
def generate_meal_plan(user: UserProfile):
    plan = generate_basic_meal_plan(user)
    return plan
