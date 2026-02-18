"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel
from typing import Optional, List


# ============================================================
# USER PROFILE SCHEMA
# ============================================================

class UserProfile(BaseModel):
    """User profile information"""
    id: Optional[int] = None  # ✅ ADDED: Telegram user ID
    name: str
    age: int
    weight: float
    height: float
    diet_type: Optional[str] = None  # veg, non-veg, vegan
    goal: Optional[str] = None  # weight_loss, muscle_gain, maintenance
    allergies: Optional[List[str]] = None
    preferences: Optional[str] = None
    phone_number: Optional[str] = None


# ============================================================
# MEAL PLAN RESPONSE SCHEMA
# ============================================================

class MealPlanResponse(BaseModel):
    """6-meal plan response"""
    breakfast: str
    breakfast_cal: int
    morning_snack: str
    morning_snack_cal: int
    lunch: str
    lunch_cal: int
    afternoon_snack: str
    afternoon_snack_cal: int
    dinner: str
    dinner_cal: int
    evening_snack: str
    evening_snack_cal: int
    total_calories: int


# ============================================================
# FOOD LOG SCHEMA
# ============================================================

class FoodLogRequest(BaseModel):
    """Food log request"""
    user_id: int
    meal_type: str
    food_name: str
    quantity: float
    unit: str


class FoodLogResponse(BaseModel):
    """Food log response"""
    status: str
    food: str
    input: str
    standard_serving: str
    actual_calories: int
    actual_protein: float
    actual_carbs: float
    actual_fats: float
    meal_type: str
    consumed_total: int
    remaining: int
    message: str


# ============================================================
# DAILY STATUS SCHEMA
# ============================================================

class MealTypeStatus(BaseModel):
    """Status for a specific meal type"""
    target: int
    consumed: int
    remaining: int
    items: List[str]


class MacroBreakdown(BaseModel):
    """Macro breakdown"""
    protein_g: float
    carbs_g: float
    fats_g: float


class DailyStatusResponse(BaseModel):
    """Daily status response"""
    status: str
    date: str
    user: str
    goal: str
    target_calories: int
    consumed_calories: int
    remaining_calories: int
    meals_by_type: dict
    meals_logged: int
    macros: MacroBreakdown
    progress: str


# ============================================================
# MEAL SUGGESTION SCHEMA
# ============================================================

class FoodSuggestion(BaseModel):
    """Single food suggestion"""
    food: str
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    cuisine: Optional[str] = None
    diet_type: Optional[str] = None


class SuggestionsResponse(BaseModel):
    """Meal suggestions response"""
    status: str
    user: str
    meal_type: str
    target_calories: int
    suggestions: List[FoodSuggestion]
