from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info (6 attributes from schemas)
    name = Column(String, index=True)
    age = Column(Integer)
    weight = Column(Float)
    height = Column(Float)
    diet_type = Column(String)  # veg / non-veg / vegan
    goal = Column(String)  # weight_loss / muscle_gain / maintain
    
    # Additional info (4 attributes from original models)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    allergies = Column(String, nullable=True)  # Stored as comma-separated string
    preferences = Column(String, nullable=True)
    
    # TOTAL: 10 attributes (id + 6 from schemas + 3 extra)
    
    # Relationship to meal plans
    meal_plans = relationship("MealPlan", back_populates="user")


class MealPlan(Base):
    __tablename__ = "meal_plans"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Meal plan details (4 attributes from schemas)
    breakfast = Column(String)
    lunch = Column(String)
    dinner = Column(String)
    total_calories = Column(Integer)
    
    # TOTAL: 6 attributes (id + user_id + 4 from schemas)
    
    # Relationship back to user
    user = relationship("User", back_populates="meal_plans")