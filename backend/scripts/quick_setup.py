"""
Quick Setup Script
Creates tables and admin user without requiring server shutdown
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from api.models.database import Base
from api.models.user import User, UserRole
from api.core.auth import PasswordManager

# Database URL from environment
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "chatbot")

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def main():
    print("=" * 60)
    print("Quick Setup - Creating tables and admin user")
    print("=" * 60)
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        # Create tables
        print("\nCreating tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables created successfully")
        
        # Create session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Check if admin user exists (no tenant needed - single organization)
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Create admin user
                print("\nCreating admin user...")
                admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "admin123")
                hashed_password = PasswordManager.hash_password(admin_password)
                
                user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=hashed_password,
                    full_name="System Administrator",
                    role=UserRole.ADMIN,
                    extra_metadata={"created_by": "quick_setup"}
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(f"✓ Created admin user: {user.username}")
                print(f"  Password: {admin_password}")
                print(f"  ⚠️  IMPORTANT: Change this password after first login!")
            else:
                print(f"✓ Admin user already exists: {user.username}")
            
            # Settings are managed in config.toml - no need to create TenantSettings
            print("\n✓ All settings are managed in config.toml")
        
        print("\n" + "=" * 60)
        print("✓ Setup completed successfully!")
        print("=" * 60)
        print("\nYou can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
