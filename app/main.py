"""Main app"""
from fastapi import FastAPI
from app.database.base import Base
from app.database.session import engine
from app.api.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Meal Planner API",
    description="AI-powered meal planning",
    version="0.1.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "MealBot is running", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}