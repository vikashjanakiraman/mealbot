from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class FoodLog(Base):
    __tablename__ = "food_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Meal information
    meal_type = Column(String, index=True)  # breakfast, morning_snack, lunch, afternoon_snack, dinner, evening_snack
    food_name = Column(String, index=True)
    calories = Column(Integer)
    
    # Macros (for future use)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fats_g = Column(Float, nullable=True)
    
    # Timestamps
    logged_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign key
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    
    # Relationship
    user = relationship("User", back_populates="food_logs")
    
    def __repr__(self):
        return f"<FoodLog(id={self.id}, user_id={self.user_id}, food={self.food_name}, cal={self.calories})>"