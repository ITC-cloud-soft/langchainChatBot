"""
ARS Service Module

This module provides functionality to fetch system prompts from ARS API
and manage prompt updates.
"""

import os
import logging
import httpx
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import database_manager
from api.models.user import get_ars_token_by_user

logger = logging.getLogger(__name__)

# ARS API endpoint from environment variable
ARS_API_ENDPOINT = os.getenv("ARS_API_ENDPOINT", "http://localhost:5050")
ARS_PROMPT_PATH = "/get_message"


class ArsService:
    """Service for interacting with ARS API"""
    
    @staticmethod
    async def fetch_system_prompt_from_ars(
        api_key: str,
        endpoint: Optional[str] = None,
        timeout: int = 30
    ) -> Optional[str]:
        """
        Fetch system prompt from ARS API
        
        Args:
            api_key: ARS API key
            endpoint: ARS API endpoint (optional, uses env var if not provided)
            timeout: Request timeout in seconds
            
        Returns:
            System prompt message or None if failed
        """
        if not api_key:
            logger.warning("ARS API key is empty")
            return None
        
        url = endpoint or f"{ARS_API_ENDPOINT}{ARS_PROMPT_PATH}"
        headers = {"X-API-Key": api_key}
        
        try:
            logger.info(f"Fetching system prompt from ARS: {url}")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                json_response = response.json()
                logger.info(f"ARS response received: {json_response}")
                
                # Check if response contains 'message' field
                if 'message' in json_response:
                    message = json_response['message']
                    logger.info(f"System prompt fetched successfully: {len(message)} characters")
                    return message
                else:
                    logger.warning("ARS response does not contain 'message' field")
                    return None
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"ARS API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"ARS API request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching from ARS: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_ars_token(db: AsyncSession, user_id: int) -> Optional[str]:
        """
        Get ARS token for a specific user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            ARS token or None
        """
        ars_token = await get_ars_token_by_user(db, user_id)
        if ars_token:
            return ars_token.token
        return None
    
    @staticmethod
    async def update_system_prompt_for_user(
        db: AsyncSession,
        user_id: int
    ) -> Optional[str]:
        """
        Update system prompt for a specific user by fetching from ARS
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Updated system prompt or None
        """
        from api.models.user import create_or_update_ars_system_prompt
        
        # Get user's ARS token
        api_key = await ArsService.get_user_ars_token(db, user_id)
        if not api_key:
            logger.info(f"No ARS token found for user {user_id}")
            return None
        
        # Fetch system prompt from ARS
        system_prompt = await ArsService.fetch_system_prompt_from_ars(api_key)
        
        if system_prompt:
            # Store the system prompt in database
            await create_or_update_ars_system_prompt(db, user_id, system_prompt)
            logger.info(f"System prompt updated and saved for user {user_id}")
            return system_prompt
        
        return None
    
    @staticmethod
    async def update_all_system_prompts():
        """
        Update system prompts for all users with ARS tokens
        This can be called by a scheduled task
        """
        logger.info("Starting system prompt update for all users")
        
        try:
            # Initialize database if needed
            if not database_manager.initialized:
                await database_manager.initialize()
            
            async with database_manager.get_db_session() as db:
                # Get all users with ARS tokens
                from api.models.user import ApiArsToken
                from sqlalchemy import select
                
                result = await db.execute(
                    select(ApiArsToken).where(ApiArsToken.token_type == 'token')
                )
                ars_tokens = result.scalars().all()
                
                logger.info(f"Found {len(ars_tokens)} users with ARS tokens")
                
                for ars_token in ars_tokens:
                    user_id = ars_token.user_id
                    try:
                        prompt = await ArsService.update_system_prompt_for_user(db, user_id)
                        if prompt:
                            logger.info(f"Updated system prompt for user {user_id}")
                        else:
                            logger.warning(f"Failed to update system prompt for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error updating prompt for user {user_id}: {str(e)}")
                        continue
                
                logger.info("System prompt update completed")
                
        except Exception as e:
            logger.error(f"Error in update_all_system_prompts: {str(e)}")
