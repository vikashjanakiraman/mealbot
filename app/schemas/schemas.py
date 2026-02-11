from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    name: str
    age: int
    weight: float
    height: float
    diet_type: str  # veg / non-veg / vegan
    goal: str       # weight_loss / muscle_gain / maintain
    allergies: Optional[List[str]] = []



class MealPlanResponse(BaseModel):
    breakfast: str
    lunch: str
    dinner: str
    total_calories: int
