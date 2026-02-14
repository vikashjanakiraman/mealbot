from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Smart Meal Planner API")

app.include_router(router)


@app.get("/")
def root():
    return {"message": "MealBot is running"}
