"""MealPlan model - with snacks"""
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(BigInteger, primary_key=True, index=True)
    
    # 6 meals per day
    breakfast = Column(String, nullable=False)
    morning_snack = Column(String, nullable=False)
    lunch = Column(String, nullable=False)
    afternoon_snack = Column(String, nullable=False)
    dinner = Column(String, nullable=False)
    evening_snack = Column(String, nullable=False)
    
    # Calorie breakdown
    breakfast_cal = Column(Integer)
    morning_snack_cal = Column(Integer)
    lunch_cal = Column(Integer)
    afternoon_snack_cal = Column(Integer)
    dinner_cal = Column(Integer)
    evening_snack_cal = Column(Integer)
    
    total_calories = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_id = Column(BigInteger, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="meal_plans")
    
    def __repr__(self):
        return f"<MealPlan(id={self.id}, total_cal={self.total_calories})>"