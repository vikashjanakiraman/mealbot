from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime

created_at = Column(DateTime(timezone=True), server_default=func.now())






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
