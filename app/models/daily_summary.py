"""DailySummary database model - aggregated daily stats"""
from sqlalchemy import Column, Integer, Float, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
from datetime import date


class DailySummary(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Date information (unique per user per day)
    date = Column(Date, default=date.today, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Calorie tracking
    target_calories = Column(Integer)
    consumed_calories = Column(Integer, default=0)
    remaining_calories = Column(Integer)
    
    # Macro aggregates
    total_protein_g = Column(Float, default=0)
    total_carbs_g = Column(Float, default=0)
    total_fats_g = Column(Float, default=0)
    
    # Meal tracking
    meals_logged = Column(Integer, default=0)  # Count of meals logged
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User")
    
    # Constraint: one summary per user per day
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='unique_user_day'),
    )
    
    def __repr__(self):
        return f"<DailySummary(user_id={self.user_id}, date={self.date}, consumed={self.consumed_calories}/{self.target_calories})>"