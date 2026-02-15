"""Pydantic schemas - WITH SNACKS"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class UserProfile(BaseModel):
    """User input/output schema"""
    name: str
    age: int
    weight: float
    height: float
    diet_type: str  # veg / non-veg / vegan
    goal: str  # weight_loss / muscle_gain / maintain
    allergies: Optional[List[str]] = []
    phone_number: Optional[str] = None
    preferences: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserProfileComplete(BaseModel):
    """Complete user profile with ID"""
    id: int
    name: str
    age: int
    weight: float
    height: float
    diet_type: str
    goal: str
    allergies: Optional[List[str]] = []
    phone_number: Optional[str] = None
    preferences: Optional[str] = None
    
    class Config:
        from_attributes = True


class MealPlanResponse(BaseModel):
    """Meal plan output schema - WITH 6 MEALS"""
    # Breakfast
    breakfast: str
    breakfast_cal: int
    
    # Morning Snack
    morning_snack: str
    morning_snack_cal: int
    
    # Lunch
    lunch: str
    lunch_cal: int
    
    # Afternoon Snack
    afternoon_snack: str
    afternoon_snack_cal: int
    
    # Dinner
    dinner: str
    dinner_cal: int
    
    # Evening Snack
    evening_snack: str
    evening_snack_cal: int
    
    # Total
    total_calories: int
    
    class Config:
        from_attributes = True


class MealPlanComplete(BaseModel):
    """Complete meal plan with ID and timestamps"""
    id: int
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
    created_at: datetime
    
    class Config:
        from_attributes = True