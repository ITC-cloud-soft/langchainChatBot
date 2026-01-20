#!/usr/bin/env python3
"""
Database migration script for chat history tables

This script provides utilities for running database migrations
using Alembic.
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from alembic import command
    from alembic.config import Config
    from api.core.database import database_manager
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def get_alembic_config():
    """Get Alembic configuration"""
    # Try current directory first (for Docker container)
    config_file = Path(__file__).parent / "alembic.ini"
    if not config_file.exists():
        # Fallback to project root
        config_file = project_root / "alembic.ini"
    
    if not config_file.exists():
        raise FileNotFoundError(f"Alembic configuration file not found: {config_file}")
    
    config = Config(str(config_file))
    return config


async def run_migration(args):
    """Run database migration"""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database manager first
        logger.info("Initializing database manager...")
        if not await database_manager.initialize():
            logger.error("Failed to initialize database manager")
            return False
        
        logger.info("Database manager initialized successfully")
        
        # Get Alembic config
        logger.info("Loading Alembic configuration...")
        config = get_alembic_config()
        
        if args.command == "upgrade":
            logger.info(f"Running upgrade to revision: {args.revision or 'head'}")
            command.upgrade(config, args.revision or "head")
            logger.info("Upgrade completed successfully")
            
        elif args.command == "downgrade":
            logger.info(f"Running downgrade to revision: {args.revision or '-1'}")
            command.downgrade(config, args.revision or "-1")
            logger.info("Downgrade completed successfully")
            
        elif args.command == "current":
            logger.info("Showing current revision...")
            command.current(config, verbose=True)
            
        elif args.command == "history":
            logger.info("Showing migration history...")
            command.history(config, verbose=True)
            
        elif args.command == "revision":
            logger.info(f"Creating new revision: {args.message}")
            command.revision(
                config,
                message=args.message,
                autogenerate=args.autogenerate
            )
            logger.info("Revision created successfully")
            
        return True
        
    except Exception as e:
        logger.error(f"Migration failed with error: {e}", exc_info=True)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup database connections
        try:
            await database_manager.close()
        except:
            pass


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Database migration script for chat history"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database schema")
    upgrade_parser.add_argument(
        "--revision", 
        help="Target revision (default: head)"
    )
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database schema")
    downgrade_parser.add_argument(
        "--revision", 
        help="Target revision (default: -1)"
    )
    
    # Current command
    subparsers.add_parser("current", help="Show current database revision")
    
    # History command
    subparsers.add_parser("history", help="Show migration history")
    
    # Revision command
    revision_parser = subparsers.add_parser("revision", help="Create new migration")
    revision_parser.add_argument(
        "--message", "-m", 
        required=True, 
        help="Migration message"
    )
    revision_parser.add_argument(
        "--autogenerate", 
        action="store_true", 
        help="Autogenerate migration from model changes"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run migration
    success = asyncio.run(run_migration(args))
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()