"""Main FastAPI app with Telegram Webhook Bot"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import existing routers
from app.api.routes import router as api_router

# Import database
from app.database.base import Base
from app.database.session import engine

# Import telegram bot
from app.telegram_bot.webhook_bot import router as telegram_router, setup_webhook

logger = logging.getLogger(__name__)


# ============================================================
# STARTUP EVENT - Register Telegram Webhook
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # STARTUP
    print("🚀 Starting MealBot API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Setup Telegram webhook
    try:
        await setup_webhook()
        print("✅ Telegram webhook registered")
    except Exception as e:
        print(f"⚠️ Telegram webhook setup failed: {e}")
    
    yield
    
    # SHUTDOWN
    print("🛑 Shutting down MealBot API...")


# ============================================================
# CREATE FASTAPI APP
# ============================================================
app = FastAPI(
    title="Smart Meal Planner API",
    description="AI-powered meal planning with Telegram bot",
    version="0.1.0",
    lifespan=lifespan
)


# ============================================================
# CORS MIDDLEWARE
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# INCLUDE ROUTERS
# ============================================================
app.include_router(api_router)  # Your meal planning API
app.include_router(telegram_router)  # Telegram webhook


# ============================================================
# ROOT ENDPOINTS
# ============================================================
@app.get("/")
def root():
    return {"message": "MealBot is running", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
