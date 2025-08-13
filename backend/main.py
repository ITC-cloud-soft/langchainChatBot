"""
FastAPI Backend for Chatbot System

This module provides the main FastAPI application for the chatbot system,
including API endpoints for chat, LLM configuration, and knowledge management.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from api.routes import chat, llm_config, knowledge, config, embedding_config
from api.core.config_manager import settings
from api.core.config_watcher import config_updater
from api.core.database import initialize_database_on_startup, cleanup_database_on_shutdown, database_manager, check_database_health
from api.services.chat_service import chat_service
from api.services.base_service import ServiceRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    
    # Reload settings to ensure environment variables are loaded
    settings.reload()
    
    # Initialize database
    db_initialized = False
    try:
        db_initialized = await initialize_database_on_startup()
        if db_initialized:
            pass
        else:
            pass
    except Exception as e:
        pass
    
    # Register and initialize services
    ServiceRegistry.register("chat_service", chat_service)
    initialization_results = await ServiceRegistry.initialize_all()
    
    # Log initialization results
    for service_name, success in initialization_results.items():
        pass
    
    yield
    # Shutdown
    # Cleanup database connections
    try:
        await cleanup_database_on_shutdown()
    except Exception as e:
        pass
    # Stop config watcher
    config_updater.stop()

# Create FastAPI app
app = FastAPI(
    title="Chatbot System API",
    description="API for a chatbot system with LLM configuration and knowledge management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(llm_config.router, prefix="/api/llm", tags=["llm-config"])
app.include_router(embedding_config.router, prefix="/api/embedding", tags=["embedding-config"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

# Mount static files for uploads
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Chatbot System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database health
        db_health = {"status": "unknown", "message": "Not initialized"}
        if database_manager.is_initialized():
            try:
                db_health = await check_database_health()
            except Exception as e:
                db_health = {"status": "unhealthy", "error": str(e)}
        
        # Check all services
        service_health = await ServiceRegistry.health_check_all()
        
        # Add database to services
        service_health["database"] = db_health
        
        # Determine overall health status
        all_healthy = all(
            result.get("status") == "healthy"
            for result in service_health.values()
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        if db_health.get("status") == "unhealthy":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "services": service_health,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD
    )