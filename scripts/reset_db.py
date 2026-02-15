"""Reset database (development only)"""
from app.database.base import Base
from app.database.session import engine
from app.models import User, MealPlan, FoodLog, DailySummary, FoodDatabase


def reset():
    """Drop all tables and recreate"""
    print("⚠️  WARNING: This will DELETE all data!")
    response = input("Type 'yes' to confirm: ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped")
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables recreated")
    
    print("\n✓ Database reset complete!")


if __name__ == "__main__":
    reset()