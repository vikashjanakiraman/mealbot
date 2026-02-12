from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    """
    Pydantic model for User input/output
    Matches User model in models.py
    """
    # Required fields (6 main attributes)
    name: str
    age: int
    weight: float
    height: float
    diet_type: str  # veg / non-veg / vegan
    goal: str  # weight_loss / muscle_gain / maintain
    
    # Optional fields (3 additional attributes)
    allergies: Optional[List[str]] = []  # List format for API, converted to string for DB
    phone_number: Optional[str] = None
    preferences: Optional[str] = None
    
    # TOTAL: 9 attributes (matches User model except id)
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


class MealPlanResponse(BaseModel):
    """
    Pydantic model for MealPlan output
    Matches MealPlan model in models.py
    """
    # All 4 meal plan attributes
    breakfast: str
    lunch: str
    dinner: str
    total_calories: int
    
    # TOTAL: 4 attributes (matches MealPlan model except id and user_id)
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


class UserProfileComplete(BaseModel):
    """
    Complete user profile including database ID
    Use this for GET endpoints that return existing users
    """
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


class MealPlanComplete(BaseModel):
    """
    Complete meal plan including database IDs
    Use this for GET endpoints that return existing meal plans
    """
    id: int
    user_id: int
    breakfast: str
    lunch: str
    dinner: str
    total_calories: int
    
    class Config:
        from_attributes = True