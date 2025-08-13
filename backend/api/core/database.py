"""
Database connection and session management for MySQL

This module provides database connection setup, session management,
and connection pooling for async MySQL operations.
"""

import os
import asyncio
from typing import Optional, AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
# import asyncmy
from tenacity import retry, stop_after_attempt, wait_exponential

from api.models.database import Base
from api.core.config_manager import settings
from api.core.utils import handle_exceptions, default_logger


class DatabaseManager:
    """
    Database manager for MySQL async operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger("database_manager")
        self.engine: Optional[create_async_engine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        self._initialized = False
        self._connection_retries = 3
        self._retry_delay = 1
    
    async def initialize(self) -> bool:
        """Initialize database connection"""
        try:
            self.logger.info("Initializing database connection...")
            
            # Get database configuration
            db_config = self._get_database_config()
            
            # Build database URL
            from urllib.parse import quote_plus
            username = quote_plus(db_config['username'])
            password = quote_plus(db_config['password'])
            host = db_config['host']
            port = db_config['port']
            database = db_config['database']
            
            # Debug: Show config (without password)
            self.logger.info(f"Database config - host: {host}, port: {port}, username: {username}, database: {database}")
            
            # Check if database exists, create if it doesn't
            if not await self._database_exists(host, port, username, password, database):
                self.logger.info(f"Database '{database}' does not exist, creating it...")
                if not await self._create_database(host, port, username, password, database):
                    self.logger.error(f"Failed to create database '{database}'")
                    return False
            
            # Build connection string with SSL parameters in connect_args
            db_url = f"mysql+aiomysql://{username}:{password}@{host}:{port}/{database}"
            
            # Debug: Show URL (without password)
            safe_url = f"mysql+aiomysql://{username}:***@{host}:{port}/{database}"
            self.logger.info(f"Database URL: {safe_url}")
            
            # Create async engine
            self.engine = create_async_engine(
                db_url,
                echo=False,  # Set to True for SQL logging
                future=True,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": False,
                    "auth_plugin": "caching_sha2_password"
                }
            )
            
            # Create async session maker
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            if await self._test_connection():
                self.logger.info("Database connection established successfully")
                self._initialized = True
                return True
            else:
                self.logger.error("Database connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            return False
    
    def _get_database_config(self) -> Dict[str, Any]:
        """Get database configuration from settings or environment variables"""
        # Debug: Check settings object
        self.logger.info(f"Settings object type: {type(settings)}")
        self.logger.info(f"Settings has database attr: {hasattr(settings, 'database')}")
        
        # Try to get from settings first
        if hasattr(settings, 'database') and hasattr(settings.database, 'host'):
            config = {
                "host": settings.database.host,
                "port": settings.database.port,
                "username": settings.database.username,
                "password": settings.database.password,
                "database": settings.database.database,
                "ssl": settings.database.ssl if hasattr(settings.database, 'ssl') else None
            }
            self.logger.info(f"Using settings config - host: {config['host']}, username: {config['username']}")
            return config
        
        # Fallback to environment variables
        return {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "username": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "chatbot"),
            "ssl": os.getenv("MYSQL_SSL", "false").lower() == "true"
        }
    
    async def _database_exists(self, host: str, port: int, username: str, password: str, database: str) -> bool:
        """Check if database exists"""
        try:
            from urllib.parse import quote_plus
            # Connect to MySQL server without specifying database
            server_url = f"mysql+aiomysql://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}"
            
            # Create temporary engine for server connection
            temp_engine = create_async_engine(
                server_url,
                echo=False,
                future=True,
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": True,
                    "auth_plugin": "caching_sha2_password"
                }
            )
            
            async with temp_engine.begin() as conn:
                # Check if database exists
                result = await conn.execute(text(f"SHOW DATABASES LIKE '{database}'"))
                exists = result.fetchone() is not None
                
            await temp_engine.dispose()
            return exists
            
        except Exception as e:
            self.logger.error(f"Error checking if database exists: {str(e)}")
            return False
    
    async def _create_database(self, host: str, port: int, username: str, password: str, database: str) -> bool:
        """Create database if it doesn't exist"""
        try:
            from urllib.parse import quote_plus
            # Connect to MySQL server without specifying database
            server_url = f"mysql+aiomysql://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}"
            
            # Create temporary engine for server connection
            temp_engine = create_async_engine(
                server_url,
                echo=False,
                future=True,
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": True,
                    "auth_plugin": "caching_sha2_password"
                }
            )
            
            async with temp_engine.begin() as conn:
                # Create database with UTF-8 support
                await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                self.logger.info(f"Database '{database}' created successfully")
                
            await temp_engine.dispose()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating database: {str(e)}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def _test_connection(self) -> bool:
        """Test database connection"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            self.logger.warning(f"Database connection test failed: {str(e)}")
            raise
    
    async def create_tables(self) -> bool:
        """Create database tables"""
        try:
            if not self._initialized:
                await self.initialize()
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self.logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating database tables: {str(e)}")
            return False
    
    async def drop_tables(self) -> bool:
        """Drop database tables"""
        try:
            if not self._initialized:
                await self.initialize()
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            self.logger.info("Database tables dropped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error dropping database tables: {str(e)}")
            return False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper error handling"""
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_connection(self):
        """Get raw database connection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.engine.connect() as conn:
                yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw SQL query"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                return result
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Test basic connection
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                test_result = result.scalar()
                
                # Get database info
                db_info = await conn.execute(text("SELECT VERSION() as version"))
                version = db_info.scalar()
                
                # Get table count
                tables = await conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()"))
                table_count = tables.scalar()
            
            return {
                "status": "healthy",
                "connection_test": test_result == 1,
                "version": version,
                "table_count": table_count,
                "message": "Database connection is healthy"
            }
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }
    
    async def close(self) -> None:
        """Close database connections"""
        try:
            if self.engine:
                await self.engine.dispose()
                self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {str(e)}")
    
    def is_initialized(self) -> bool:
        """Check if database manager is initialized"""
        return self._initialized
    
    async def backup_database(self, backup_path: str) -> bool:
        """Create a database backup"""
        try:
            # This is a simple implementation using mysqldump
            # In production, you might want to use more sophisticated backup tools
            import subprocess
            
            config = self._get_database_config()
            cmd = [
                "mysqldump",
                f"--host={config['host']}",
                f"--port={config['port']}",
                f"--user={config['username']}",
                f"--password={config['password']}",
                "--single-transaction",
                "--routines",
                "--triggers",
                config['database'],
                ">", backup_path
            ]
            
            # Execute backup command
            process = await asyncio.create_subprocess_shell(
                " ".join(cmd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Database backup created successfully at {backup_path}")
                return True
            else:
                self.logger.error(f"Database backup failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating database backup: {str(e)}")
            return False


# Global database manager instance
database_manager = DatabaseManager()


# Convenience functions for database operations
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection"""
    async with database_manager.get_session() as session:
        yield session


async def init_database() -> bool:
    """Initialize database and create tables"""
    return await database_manager.create_tables()


async def check_database_health() -> Dict[str, Any]:
    """Check database health"""
    return await database_manager.health_check()


@handle_exceptions(default_logger)
async def execute_db_query(query: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Execute database query with error handling"""
    return await database_manager.execute_query(query, params)


# Initialize database on module import
async def initialize_database_on_startup():
    """Initialize database when the application starts"""
    try:
        default_logger.info("Starting database initialization...")
        
        # Initialize database connection (includes auto-creation)
        success = await database_manager.initialize()
        if not success:
            default_logger.error("Failed to initialize database connection")
            return False
        
        # Create tables
        table_success = await database_manager.create_tables()
        if not table_success:
            default_logger.error("Failed to create database tables")
            return False
        
        default_logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        default_logger.error(f"Database initialization error: {str(e)}")
        return False


# Cleanup database on application shutdown
async def cleanup_database_on_shutdown():
    """Cleanup database connections when the application shuts down"""
    try:
        await database_manager.close()
        default_logger.info("Database connections cleaned up")
    except Exception as e:
        default_logger.error(f"Database cleanup error: {str(e)}")