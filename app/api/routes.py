"""Routes - with snacks"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.schemas import UserProfile, MealPlanResponse
from app.services.services import (
    generate_meal_plan_with_snacks,
    create_or_get_user,
    save_meal_plan
)
from app.database.session import get_db

router = APIRouter()


@router.post("/meal-plan", response_model=MealPlanResponse)
def create_meal_plan(user: UserProfile, db: Session = Depends(get_db)):
    """Create meal plan with snacks"""
    db_user = create_or_get_user(db, user)
    plan = generate_meal_plan_with_snacks(user)
    save_meal_plan(db, db_user.id, plan)
    return plan