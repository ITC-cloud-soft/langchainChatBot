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
from api.routes import chat, llm_config, knowledge, config, embedding_config, auth, users, ars_settings
from api.controllers import notification_controller
from api.core.config_manager import settings
from api.core.config_watcher import config_updater
from api.core.database import initialize_database_on_startup, cleanup_database_on_shutdown, database_manager, check_database_health
from api.services.chat_service import chat_service
from api.services.base_service import ServiceRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    import logging
    logger = logging.getLogger("chatbot_app")
    
    # Reload settings to ensure environment variables are loaded
    settings.reload()
    
    # Initialize database
    db_initialized = False
    try:
        db_initialized = await initialize_database_on_startup()
        if db_initialized:
            logger.info("Database initialized successfully")
            
            # Auto-create admin user if not exists
            try:
                from api.core.database import get_db_session
                from api.models.user import User, UserRole, get_user_by_username, create_user
                from api.core.auth import PasswordManager
                import os
                
                async for db in get_db_session():
                    # Check if admin user exists
                    admin_user = await get_user_by_username(db, "admin")
                    if not admin_user:
                        logger.info("Admin user not found, creating default admin...")
                        admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "admin123")
                        hashed_password = PasswordManager.hash_password(admin_password)
                        
                        await create_user(
                            db=db,
                            username="admin",
                            email="admin@example.com",
                            hashed_password=hashed_password,
                            full_name="System Administrator",
                            role=UserRole.ADMIN
                        )
                        logger.info("✓ Default admin user created successfully")
                        logger.info(f"  Username: admin")
                        logger.info(f"  Password: {admin_password}")
                        logger.warning("⚠️  IMPORTANT: Change this password after first login!")
                    else:
                        logger.info("Admin user already exists")
                    break
            except Exception as e:
                logger.warning(f"Could not auto-create admin user: {e}")
        else:
            logger.warning("Database initialization failed")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Register and initialize services
    ServiceRegistry.register("chat_service", chat_service)
    initialization_results = await ServiceRegistry.initialize_all()
    
    # Log initialization results
    for service_name, success in initialization_results.items():
        if success:
            logger.info(f"Service '{service_name}' initialized successfully")
        else:
            logger.warning(f"Service '{service_name}' initialization failed")
    
    # Start ARS scheduler if database is initialized
    if db_initialized:
        try:
            from api.tasks.ars_scheduler import start_ars_scheduler
            # Update system prompts every 30 minutes
            update_interval = int(os.getenv("ARS_UPDATE_INTERVAL_MINUTES", "30"))
            start_ars_scheduler(update_interval_minutes=update_interval)
            logger.info(f"ARS scheduler started with {update_interval} minute interval")
        except Exception as e:
            logger.warning(f"Failed to start ARS scheduler: {e}")
    
    yield
    # Shutdown
    # Stop ARS scheduler
    try:
        from api.tasks.ars_scheduler import stop_ars_scheduler
        stop_ars_scheduler()
        logger.info("ARS scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping ARS scheduler: {e}")
    
    # Cleanup database connections
    try:
        await cleanup_database_on_shutdown()
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")
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

# Authentication routes (public)
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

# User management routes (require authentication, admin for write)
app.include_router(users.router, prefix="/api/users", tags=["users"])

# Notification routes (require authentication)
app.include_router(notification_controller.router, prefix="/api/notifications", tags=["notifications"])

# Existing routes (will be updated for tenant context)
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(llm_config.router, prefix="/api/llm", tags=["llm-config"])
app.include_router(embedding_config.router, prefix="/api/embedding", tags=["embedding-config"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(ars_settings.router, prefix="/api", tags=["ars-settings"])

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