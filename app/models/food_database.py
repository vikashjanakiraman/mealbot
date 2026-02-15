"""FoodDatabase model - reference database of foods with nutritional info"""
from sqlalchemy import Column, Integer, String, Float
from app.database.base import Base


class FoodDatabase(Base):
    __tablename__ = "food_database"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Food identification (searchable, unique)
    food_name = Column(String, unique=True, index=True)
    
    # Nutritional info (per 100g or standard serving)
    default_calories = Column(Integer)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fats_g = Column(Float)
    
    # Categorization
    category = Column(String, index=True)  # breakfast, morning_snack, lunch, afternoon_snack, dinner, evening_snack, snack
    cuisine = Column(String, nullable=True)  # Indian, Western, etc.
    diet_type = Column(String, nullable=True)  # veg, non-veg, vegan
    
    # Search aliases (semicolon-separated for fuzzy matching)
    # e.g., "briyani;biriyani" so "briyani" finds "Biryani"
    aliases = Column(String, nullable=True, index=True)
    
    def __repr__(self):
        return f"<Food(food={self.food_name}, cal={self.default_calories}, protein={self.protein_g}g)>"