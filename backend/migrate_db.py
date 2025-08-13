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
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from alembic import command
    from alembic.config import Config
    from api.core.database import database_manager
except ImportError as e:
    sys.exit(1)


def get_alembic_config():
    """Get Alembic configuration"""
    config_file = project_root / "alembic.ini"
    if not config_file.exists():
        raise FileNotFoundError(f"Alembic configuration file not found: {config_file}")
    
    config = Config(str(config_file))
    return config


async def run_migration(args):
    """Run database migration"""
    try:
        # Initialize database manager first
        if not await database_manager.initialize():
            return False
        
        # Get Alembic config
        config = get_alembic_config()
        
        if args.command == "upgrade":
            command.upgrade(config, args.revision or "head")
            
        elif args.command == "downgrade":
            command.downgrade(config, args.revision or "-1")
            
        elif args.command == "current":
            command.current(config, verbose=True)
            
        elif args.command == "history":
            command.history(config, verbose=True)
            
        elif args.command == "revision":
            command.revision(
                config,
                message=args.message,
                autogenerate=args.autogenerate
            )
            
        return True
        
    except Exception as e:
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