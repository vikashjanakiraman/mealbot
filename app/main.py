from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import traceback

# Import database utilities
from app.database import engine, get_db, Base

# Import SQLAlchemy models
from app.models.models import User, MealPlan

# Import Pydantic schemas
from app.schemas.schemas import UserProfile, MealPlanResponse

# Import services
from app.services.services import generate_basic_meal_plan

# Create all tables in database
print("🔧 Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"❌ Error creating tables: {e}")
    raise

app = FastAPI(title="Smart Meal Planner API")


@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "message": "Meal Planner API is running 🚀",
        "status": "healthy"
    }


@app.post("/generate-meal-plan", response_model=MealPlanResponse)
def generate_meal_plan(user: UserProfile, db: Session = Depends(get_db)):
    """
    Generate a personalized meal plan based on user profile
    
    This endpoint:
    1. Receives UserProfile data
    2. Generates meal plan using service layer
    3. Saves user to database
    4. Saves meal plan to database
    5. Returns MealPlanResponse
    """
    
    try:
        print(f"📥 Received request for user: {user.name}")
        
        # Step 1: Generate the meal plan
        print("🍽️  Generating meal plan...")
        plan = generate_basic_meal_plan(user)
        print(f"✅ Meal plan generated: {plan.total_calories} calories")
        
        # Step 2: Create user object with ALL attributes
        print("👤 Creating user in database...")
        db_user = User(
            name=user.name,
            age=user.age,
            weight=user.weight,
            height=user.height,
            diet_type=user.diet_type,
            goal=user.goal,
            allergies=",".join(user.allergies) if user.allergies else None,
            phone_number=user.phone_number if hasattr(user, 'phone_number') else None,
            preferences=user.preferences if hasattr(user, 'preferences') else None
        )
        
        # Step 3: Save user to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"✅ User created with ID: {db_user.id}")
        
        # Step 4: Create meal plan linked to user
        print("📋 Saving meal plan to database...")
        db_meal = MealPlan(
            user_id=db_user.id,
            breakfast=plan.breakfast,
            lunch=plan.lunch,
            dinner=plan.dinner,
            total_calories=plan.total_calories
        )
        
        # Step 5: Save meal plan to database
        db.add(db_meal)
        db.commit()
        db.refresh(db_meal)
        print(f"✅ Meal plan saved with ID: {db_meal.id}")
        
        print("🎉 Request completed successfully")
        return plan
        
    except AttributeError as e:
        error_msg = f"Attribute error: {str(e)}. Check if User model has all required fields."
        print(f"❌ {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)
        
    except ImportError as e:
        error_msg = f"Import error: {str(e)}. Check your import paths."
        print(f"❌ {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)
        
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        allergies_list = user.allergies.split(",") if user.allergies else []
        
        return {
            "id": user.id,
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "height": user.height,
            "diet_type": user.diet_type,
            "goal": user.goal,
            "allergies": allergies_list,
            "phone_number": user.phone_number,
            "preferences": user.preferences
        }
    except Exception as e:
        print(f"❌ Error fetching user: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/meal-plans")
def get_user_meal_plans(user_id: int, db: Session = Depends(get_db)):
    """Get all meal plans for a specific user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        meal_plans = db.query(MealPlan).filter(MealPlan.user_id == user_id).all()
        
        return [
            {
                "id": meal.id,
                "breakfast": meal.breakfast,
                "lunch": meal.lunch,
                "dinner": meal.dinner,
                "total_calories": meal.total_calories
            }
            for meal in meal_plans
        ]
    except Exception as e:
        print(f"❌ Error fetching meal plans: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/tables")
def debug_tables():
    """Debug endpoint to check database tables"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        table_info = {}
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            table_info[table_name] = [col['name'] for col in columns]
        
        return {
            "tables": tables,
            "table_info": table_info
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug/test-db")
def test_database():
    """Test database connection"""
    try:
        db = next(get_db())
        # Try a simple query
        user_count = db.query(User).count()
        meal_count = db.query(MealPlan).count()
        
        return {
            "status": "connected",
            "user_count": user_count,
            "meal_plan_count": meal_count
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)