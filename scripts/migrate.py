"""Migration script - create tables and indexes"""
from sqlalchemy import inspect, text
from app.database.session import engine
from app.database.base import Base
from app.models import User, MealPlan, FoodLog, DailySummary, FoodDatabase


def migrate():
    """Create all tables and indexes"""
    print("="*60)
    print("MEALBOT DATABASE MIGRATION")
    print("="*60)
    
    print("\n1. Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("   ✓ All tables created")
    
    print("\n2. Verifying tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['users', 'meal_plans', 'food_logs', 'daily_summaries', 'food_database']
    
    for table in required_tables:
        if table in tables:
            cols = [c['name'] for c in inspector.get_columns(table)]
            print(f"   ✓ {table}: {len(cols)} columns")
        else:
            print(f"   ✗ {table}: MISSING!")
            return False
    
    print("\n3. Creating indexes...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_phone ON users(phone_number)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_foodlog_user ON food_logs(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_foodlog_logged_at ON food_logs(logged_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_daily_user_date ON daily_summaries(user_id, date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_food_name ON food_database(food_name)"))
            conn.commit()
        print("   ✓ All indexes created")
    except Exception as e:
        print(f"   ⚠ Index creation: {e}")
    
    print("\n" + "="*60)
    print("✓ MIGRATION COMPLETE")
    print("="*60)
    return True


if __name__ == "__main__":
    migrate()