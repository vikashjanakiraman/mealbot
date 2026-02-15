"""User database model"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String, index=True)
    age = Column(Integer)
    weight = Column(Float)  # in kg
    height = Column(Float)  # in cm
    diet_type = Column(String)  # veg / non-veg / vegan
    goal = Column(String)  # weight_loss / muscle_gain / maintain
    
    # Additional info
    phone_number = Column(String, unique=True, index=True, nullable=True)
    allergies = Column(String, nullable=True)  # comma-separated: "nuts,dairy"
    preferences = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships (ADD THIS)
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")
    food_logs = relationship("FoodLog", back_populates="user", cascade="all, delete-orphan")  # NEW LINE
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, phone={self.phone_number})>"