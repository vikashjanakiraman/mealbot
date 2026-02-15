"""Validate database schema"""
from sqlalchemy import inspect
from app.database.session import engine
import sys


REQUIRED_SCHEMA = {
    'users': ['id', 'name', 'age', 'weight', 'height', 'diet_type', 'goal', 'phone_number'],
    'meal_plans': ['id', 'breakfast', 'breakfast_cal', 'morning_snack', 'morning_snack_cal', 
                   'lunch', 'lunch_cal', 'afternoon_snack', 'afternoon_snack_cal', 
                   'dinner', 'dinner_cal', 'evening_snack', 'evening_snack_cal', 'total_calories', 'user_id'],
    'food_logs': ['id', 'meal_type', 'food_name', 'calories', 'protein_g', 'carbs_g', 'fats_g', 'user_id', 'logged_at'],
    'daily_summaries': ['id', 'date', 'user_id', 'target_calories', 'consumed_calories', 'remaining_calories'],
    'food_database': ['id', 'food_name', 'default_calories', 'protein_g', 'carbs_g', 'fats_g', 'category'],
}


def validate():
    """Validate entire schema"""
    print("="*60)
    print("SCHEMA VALIDATION")
    print("="*60)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    all_valid = True
    
    for table_name, required_cols in REQUIRED_SCHEMA.items():
        print(f"\n{table_name}:")
        
        if table_name not in tables:
            print(f"  ✗ TABLE NOT FOUND")
            all_valid = False
            continue
        
        columns = {c['name'] for c in inspector.get_columns(table_name)}
        
        for col in required_cols:
            if col in columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} MISSING")
                all_valid = False
    
    print("\n" + "="*60)
    if all_valid:
        print("✓ ALL VALIDATIONS PASSED")
        print("="*60)
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(validate())