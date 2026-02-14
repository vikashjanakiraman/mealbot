from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime

created_at = Column(DateTime(timezone=True), server_default=func.now())





class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    breakfast = Column(String, nullable=False)
    lunch = Column(String, nullable=False)
    dinner = Column(String, nullable=False)
    total_calories = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="meal_plans")
