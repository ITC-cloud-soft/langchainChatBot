"""
Authentication and authorization utilities

This module provides JWT token generation/validation, password hashing,
and user authentication functionality for the single organization system.
"""

import os
import warnings
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status

# Suppress bcrypt version warning
import logging
logging.getLogger("passlib").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=Warning)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration (from environment variables)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class PasswordManager:
    """Password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """JWT token generation and validation"""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Payload data to encode in the token
            expires_delta: Token expiration time delta
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token
        
        Args:
            data: Payload data to encode in the token
            expires_delta: Token expiration time delta
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            raise HTTPException(
            )
    
    @staticmethod
    def create_token_pair(user_id: int, role: str) -> Dict[str, str]:
        """
        Create both access and refresh tokens
        
        Args:
            user_id: User ID
            role: User role (admin/user)
            
        Returns:
            Dictionary with access_token, refresh_token, and token_type
        """
        token_data = {
            "sub": str(user_id),
            "role": role
        }
        
        access_token = TokenManager.create_access_token(token_data)
        refresh_token = TokenManager.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


class AuthorizationManager:
    """Role-based access control"""
    
    @staticmethod
    def is_admin(role: str) -> bool:
        """Check if user has admin role"""
        return role.lower() == "admin"
    
    @staticmethod
    def is_user(role: str) -> bool:
        """Check if user has user role"""
        return role.lower() == "user"
    
    @staticmethod
    def can_manage_tenant(role: str) -> bool:
        """Check if user can manage tenant settings"""
        return role.lower() == "admin"
    
    @staticmethod
    def require_admin(role: str) -> None:
        """Raise exception if user is not admin"""
        if not AuthorizationManager.is_admin(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator privileges required"
            )


def create_initial_admin(
    username: str = "admin",
    email: str = "admin@example.com",
    password: str = "admin123",
    full_name: str = "System Administrator"
) -> Dict[str, Any]:
    """
    Create initial admin credentials
    Used for first-time setup
    
    Returns:
        Dictionary with admin user information
    """
    hashed_password = PasswordManager.hash_password(password)
    
    return {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "full_name": full_name,
        "role": "admin"
    }


# Convenience functions
def hash_password(password: str) -> str:
    """Hash a password"""
    return PasswordManager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return PasswordManager.verify_password(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any]) -> str:
    """Create an access token"""
    return TokenManager.create_access_token(data)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode a token"""
    return TokenManager.decode_token(token)
