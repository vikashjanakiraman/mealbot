from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import traceback

# Import database utilities
from app.database import engine, get_db, Base

# Import SQLAlchemy models
from app.models.models import User, MealPlan

# Import Pydantic schemas
from app.schemas.schemas import UserProfile, MealPlanResponse, MealPlanComplete

# Import services
from app.services.services import (
    generate_basic_meal_plan,
    create_or_get_user,
    save_meal_plan
)


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
    try:
        # Create or fetch user
        db_user = create_or_get_user(db, user)

        # Generate plan
        plan = generate_basic_meal_plan(user)

        # Save meal plan
        save_meal_plan(db, db_user.id, plan)

        return plan

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/users/{user_id}/meal-plans", response_model=list[MealPlanComplete])
def get_user_meal_plans(user_id: int, db: Session = Depends(get_db)):
    
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.meal_plans



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