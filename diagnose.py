#!/usr/bin/env python3
"""
Diagnostic script to identify API issues
Run this with: python3 diagnose.py
"""

import sys
import os

print("🔍 MEAL PLANNER API DIAGNOSTICS")
print("=" * 60)

# Check 1: Python version
print("\n1️⃣ Checking Python version...")
print(f"   Python: {sys.version}")
if sys.version_info < (3, 7):
    print("   ❌ Python 3.7+ required!")
else:
    print("   ✅ Python version OK")

# Check 2: Required packages
print("\n2️⃣ Checking installed packages...")
required_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic']
for package in required_packages:
    try:
        __import__(package)
        print(f"   ✅ {package} installed")
    except ImportError:
        print(f"   ❌ {package} NOT installed - run: pip install {package}")

# Check 3: File structure
print("\n3️⃣ Checking file structure...")
required_files = [
    'app/__init__.py',
    'app/main.py',
    'app/database.py',
    'app/models/__init__.py',
    'app/models/models.py',
    'app/schemas/__init__.py',
    'app/schemas/schemas.py',
    'app/services/__init__.py',
    'app/services/services.py',
]

for file_path in required_files:
    if os.path.exists(file_path):
        print(f"   ✅ {file_path}")
    else:
        print(f"   ❌ {file_path} MISSING")

# Check 4: Import test
print("\n4️⃣ Testing imports...")
try:
    from app.database import Base, engine, get_db
    print("   ✅ Database imports OK")
except Exception as e:
    print(f"   ❌ Database import failed: {e}")

try:
    from app.models.models import User, MealPlan
    print("   ✅ Models imports OK")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")

try:
    from app.schemas.schemas import UserProfile, MealPlanResponse
    print("   ✅ Schemas imports OK")
except Exception as e:
    print(f"   ❌ Schemas import failed: {e}")

try:
    from app.services.services import generate_basic_meal_plan
    print("   ✅ Services imports OK")
except Exception as e:
    print(f"   ❌ Services import failed: {e}")

# Check 5: Database tables
print("\n5️⃣ Checking database...")
try:
    from sqlalchemy import inspect
    from app.database import engine
    
    if os.path.exists('meal_planner.db'):
        print("   ✅ Database file exists")
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   Tables: {tables}")
        
        if 'users' in tables:
            columns = [col['name'] for col in inspector.get_columns('users')]
            print(f"   User columns ({len(columns)}): {columns}")
            
            expected = ['id', 'name', 'age', 'weight', 'height', 'diet_type', 'goal', 'phone_number', 'allergies', 'preferences']
            missing = [col for col in expected if col not in columns]
            if missing:
                print(f"   ❌ MISSING COLUMNS: {missing}")
                print(f"   🔧 FIX: Delete meal_planner.db and restart server")
            else:
                print(f"   ✅ All user columns present")
        else:
            print("   ❌ Users table not found")
            
        if 'meal_plans' in tables:
            columns = [col['name'] for col in inspector.get_columns('meal_plans')]
            print(f"   MealPlan columns ({len(columns)}): {columns}")
            print(f"   ✅ Meal plans table exists")
        else:
            print("   ❌ Meal plans table not found")
    else:
        print("   ⚠️  Database file doesn't exist (will be created on first run)")
except Exception as e:
    print(f"   ❌ Database check failed: {e}")

# Check 6: Test service function
print("\n6️⃣ Testing service function...")
try:
    from app.schemas.schemas import UserProfile, MealPlanResponse
    from app.services.services import generate_basic_meal_plan
    
    test_user = UserProfile(
        name="Test",
        age=25,
        weight=70.0,
        height=170.0,
        diet_type="veg",
        goal="weight_loss",
        allergies=[]
    )
    
    result = generate_basic_meal_plan(test_user)
    
    if isinstance(result, MealPlanResponse):
        print(f"   ✅ Service returns MealPlanResponse object")
        print(f"   Breakfast: {result.breakfast[:50]}...")
        print(f"   Calories: {result.total_calories}")
    elif isinstance(result, dict):
        print(f"   ❌ Service returns dict, not MealPlanResponse!")
        print(f"   🔧 FIX: Change return statement in services.py to return MealPlanResponse(...)")
    else:
        print(f"   ❌ Service returns unexpected type: {type(result)}")
        
except Exception as e:
    print(f"   ❌ Service test failed: {e}")
    import traceback
    traceback.print_exc()

# Check 7: Test database connection
print("\n7️⃣ Testing database connection...")
try:
    from app.database import SessionLocal
    from app.models.models import User
    
    db = SessionLocal()
    count = db.query(User).count()
    print(f"   ✅ Database connection OK")
    print(f"   Users in database: {count}")
    db.close()
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTICS COMPLETE")
print("\n💡 NEXT STEPS:")
print("   1. Fix any ❌ errors shown above")
print("   2. If database columns are missing, run: rm meal_planner.db")
print("   3. Restart server: uvicorn app.main:app --reload")
print("   4. Share the output if you need more help")