"""FoodDatabase model - reference database of foods with serving sizes"""
from sqlalchemy import Column, Integer, String, Float
from app.database.base import Base


class FoodDatabase(Base):
    __tablename__ = "food_database"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Food identification
    food_name = Column(String, unique=True, index=True)
    
    # Serving size (STANDARDIZED) - NEW COLUMNS
    serving_size = Column(Integer, default=100)  # e.g., 100, 200, 300 (in grams)
    serving_unit = Column(String, default="grams")  # "grams", "bowl", "cup", "piece", "plate"
    serving_description = Column(String, default="1 serving")  # "1 cup", "1 medium bowl", "100g"
    
    # Nutritional info (PER SERVING)
    default_calories = Column(Integer)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fats_g = Column(Float)
    
    # Categorization
    category = Column(String, index=True)
    cuisine = Column(String, nullable=True)
    diet_type = Column(String, nullable=True)
    aliases = Column(String, nullable=True, index=True)
    
    def __repr__(self):
        return f"<Food(food={self.food_name}, serving={self.serving_description}, cal={self.default_calories})>"