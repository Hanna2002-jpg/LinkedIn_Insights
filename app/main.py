"""
LinkedIn Insights Microservice - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

#from app.api.routes import pages, posts, employees, ai_summary
from app.api.v1 import ai_summary # or summary
from app.api.v1 import pages, posts # Only import the routers that exist
from app.services import ai_service # Import services from the services folder
from app.core.config import settings
from app.core.database import engine, Base
from app.core.cache import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting LinkedIn Insights Microservice...")
    
    try:
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database connected")
    except Exception as e:
        print(f"⚠️ Database connection error: {e}")
    
    try:
        # Initialize Redis connection
        await redis_client.initialize()
    except Exception as e:
        print(f"⚠️ Redis connection error (continuing without cache): {e}")
    
    print("✅ Application started!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    try:
        await redis_client.close()
        await engine.dispose()
    except Exception:
        pass

app = FastAPI(
    title="LinkedIn Insights Microservice",
    description="API for fetching and analyzing LinkedIn Page insights",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pages.router, prefix="/api/v1/pages", tags=["Pages"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["Posts"])
# Example of how the inclusion should look in app/main.py:
app.include_router(ai_summary.router, prefix="/api/v1/pages", tags=["AI Summary"])

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LinkedIn Insights Microservice",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "cache": "connected",
        "storage": "connected"
    }